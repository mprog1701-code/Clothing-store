from django import forms
from .models import Address

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
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '05xxxxxxxx',
            'pattern': '05[0-9]{8}',
            'maxlength': '10'
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
            if not phone.startswith('05'):
                raise forms.ValidationError('رقم الجوال يجب أن يبدأ بـ 05')
            if len(phone) != 10:
                raise forms.ValidationError('رقم الجوال يجب أن يكون 10 أرقام')
        return phone