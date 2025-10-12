from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from .models import CustomUser, Product, Order, OrderItem
from django.db.models.signals import post_save, post_delete
import os
from django.conf import settings


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Campos a mostrar en la lista de usuarios
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role')
    # Campos editables en el formulario de creación/edición
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )

class OrderItemInlineFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure that price is set if product is selected
        for form in self.forms:
            if 'product' in form.fields:
                form.fields['product'].required = True
            if 'price' in form.fields:
                form.fields['price'].required = False  
    def clean(self):
        super().clean()
        for form in self.forms:
            if form.cleaned_data and 'product' in form.cleaned_data:
                product = form.cleaned_data['product']
                if product and not form.cleaned_data.get('price'):
                    # If product is selected but price is not set, set it to the product's current price
                    form.cleaned_data['price'] = product.price
            if 'quantity' in form.cleaned_data and form.cleaned_data['quantity'] <= 0:
                raise forms.ValidationError("Quantity must be greater than zero.")

    def get_readonly_fields(self, request, obj=None):
        if obj:  # If the order item already exists
            return self.readonly_fields + ('product', 'price')
        return self.readonly_fields
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if instance.product and not instance.price:
                instance.price = instance.product.price
            instance.save()
        formset.save_m2m()


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ('product', 'price', 'quantity', 'subtotal')
    readonly_fields = ('subtotal','price') 
    show_change_link = True
    can_delete = True
    verbose_name = 'Order Item'
    verbose_name_plural = 'Order Items'
    formset = OrderItemInlineFormSet  # Custom formset to handle price at time of order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'order_date', 'status', 'amount')
    list_filter = ('status', 'order_date')
    search_fields = ('customer_name', 'id')
    inlines = [OrderItemInline]
    readonly_fields = ('amount', 'endTime') # El total se calcula
    fieldsets = (
        (None, {
            'fields': ('customer_name', 'tableNumber', 'status', 'amount', 'IP', 'initialTime', 'endTime', 'order_date')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Prefetch related order_items and their products, and select related status
        return qs.select_related('status').prefetch_related('order_items__product')
       
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # After saving all inlines, update the amount
        order = form.instance
        total = sum(item.subtotal for item in order.order_items.all())
        order.amount = total
        order.save()

class ProductAdminForm(forms.ModelForm):
    existing_image = forms.ChoiceField(
        choices=[],
        required=False,
        label="Usar imagen existente"
    )

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Buscar imágenes existentes en la carpeta
        images_path = os.path.join(settings.MEDIA_ROOT, 'products')
        if os.path.exists(images_path):
            images = [
                (f'products/{img}', img)
                for img in os.listdir(images_path)
                if os.path.isfile(os.path.join(images_path, img))
            ]
            self.fields['existing_image'].choices = [('', '---')] + images

    def clean(self):
        cleaned_data = super().clean()
        existing_image = cleaned_data.get('existing_image')
        image = cleaned_data.get('image')
        # Si se selecciona una imagen existente y no se sube una nueva
        if existing_image and not image:
            self.instance.image.name = existing_image
            cleaned_data['image'] = None  # Evita crear una nueva imagen
        return cleaned_data


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'price', 'stock')
    search_fields = ('name',)

admin.site.register(CustomUser, CustomUserAdmin)
# Product y Order ya están registrados con @admin.register



