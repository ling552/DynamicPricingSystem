from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Product, SalesRecord


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})


class LoginForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        if "username" in self.fields:
            self.fields["username"].widget.attrs.update({"class": "form-control"})
        if "password" in self.fields:
            self.fields["password"].widget.attrs.update({"class": "form-control"})


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "price", "cost", "category", "price_sensitivity"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "cost": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "price_sensitivity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }


class SalesRecordForm(forms.ModelForm):
    class Meta:
        model = SalesRecord
        fields = ["product", "sale_date", "price", "quantity"]
        widgets = {
            "product": forms.Select(attrs={"class": "form-select"}),
            "sale_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
        }


class SimulationForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.none())
    price_change_rate = forms.FloatField(
        label="调整比例(%)",
        help_text="例如 10 表示 +10%，-5 表示 -5%",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].widget.attrs.update({"class": "form-select"})
        self.fields["price_change_rate"].widget.attrs.update({"class": "form-control"})
        if user is not None:
            self.fields["product"].queryset = Product.objects.filter(created_by=user)

    def clean_price_change_rate(self):
        v = float(self.cleaned_data["price_change_rate"])
        return v / 100.0


class AnalysisFilterForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(), required=False, label="商品"
    )
    start_date = forms.DateField(
        required=False,
        label="开始日期",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    end_date = forms.DateField(
        required=False,
        label="结束日期",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].widget.attrs.update({"class": "form-select"})
        if user is not None:
            self.fields["product"].queryset = Product.objects.filter(created_by=user)
