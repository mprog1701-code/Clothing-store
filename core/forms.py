from django import forms
from django.forms import inlineformset_factory
from .models import Address, Product, ProductVariant, ProductImage

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['city', 'area', 'street', 'details']
        widgets = {
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المدينة'
            }),
            'area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الحي أو المنطقة'
            }),
            'street': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الشارع'
            }),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'تفاصيل إضافية لتسهيل الوصول (اختياري)'
            })
        }
    
    # Add extra fields not in the model for better user experience
    title = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'مثال: المنزل، العمل'
        }),
        help_text='اسم مميز للعنوان',
        required=False
    )
    
    recipient_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم المستلم الكامل'
        }),
        help_text='اسم الشخص الذي سيتسلم الطلب',
        required=False
    )
    
    phone = forms.CharField(
        max_length=11,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '07xxxxxxxxx',
            'pattern': '07[0-9]{9}',
            'maxlength': '11'
        }),
        help_text='رقم الجوال للتواصل',
        required=False
    )
    
    postal_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'الرمز البريدي'
        }),
        required=False
    )
    
    is_default = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        initial=False
    )
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            if not phone.startswith('07'):
                raise forms.ValidationError('رقم الجوال يجب أن يبدأ بـ 07')
            if len(phone) != 11:
                raise forms.ValidationError('رقم الجوال يجب أن يكون 11 رقماً')
        return phone


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'base_price', 'discount_price', 'size_type', 'fit_type', 'is_active', 'is_featured']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'size_type': forms.Select(attrs={'class': 'form-select'}),
            'fit_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['color_attr', 'size_attr', 'size', 'stock_qty', 'price_override', 'is_enabled']
        widgets = {
            'color_attr': forms.Select(attrs={'class': 'form-select'}),
            'size_attr': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_qty': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'price_override': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'image_url', 'video_file', 'video_url', 'color_attr', 'variant', 'is_main', 'order']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control'}),
            'video_file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'video/*'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'color_attr': forms.Select(attrs={'class': 'form-select'}),
            'variant': forms.Select(attrs={'class': 'form-select'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


VariantFormSet = inlineformset_factory(Product, ProductVariant, form=ProductVariantForm, extra=1, can_delete=True)
ImageFormSet = inlineformset_factory(Product, ProductImage, form=ProductImageForm, extra=1, can_delete=True)
