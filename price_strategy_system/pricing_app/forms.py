from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Product, SalesRecord

# 保留账号：用户名不可修改，且任何低于超级管理员的角色都不能编辑这些账号
RESERVED_USERNAMES = {"root", "demo"}


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


class ProfileForm(forms.ModelForm):
    """普通用户在 /profile/ 页面修改自己的基本信息。"""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "姓",
            "last_name": "名",
            "email": "邮箱",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "姓"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "名"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@example.com"}),
        }


class ProfilePasswordForm(forms.Form):
    """用户在 /profile/ 修改自己密码（可选）。"""

    old_password = forms.CharField(
        label="当前密码",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}),
    )
    new_password1 = forms.CharField(
        label="新密码",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    new_password2 = forms.CharField(
        label="确认新密码",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        old_pwd = cleaned.get("old_password") or ""
        new1 = cleaned.get("new_password1") or ""
        new2 = cleaned.get("new_password2") or ""

        # 三个都为空时表示用户不修改密码，跳过校验
        if not old_pwd and not new1 and not new2:
            cleaned["change_password"] = False
            return cleaned

        if not old_pwd:
            self.add_error("old_password", "请输入当前密码")
        elif self.user and not self.user.check_password(old_pwd):
            self.add_error("old_password", "当前密码不正确")

        if new1 != new2:
            self.add_error("new_password2", "两次输入的新密码不一致")

        if new1:
            try:
                validate_password(new1, user=self.user)
            except ValidationError as exc:
                self.add_error("new_password1", exc)

        cleaned["change_password"] = True
        return cleaned


class AdminUserForm(forms.ModelForm):
    """超级管理员/管理员维护其他用户的资料表单。

    权限矩阵：
    - 超级管理员：可修改任何用户的所有字段，但不能取消自己的超管权限/启用状态；
      不能修改 root / demo 的用户名。
    - 管理员（is_staff 且非 superuser）：只能编辑普通用户和其他管理员；
      不能修改超级管理员；不能将他人提升为超级管理员；
      不能修改 root / demo 的用户名。
    """

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
        )
        labels = {
            "username": "用户名",
            "first_name": "姓",
            "last_name": "名",
            "email": "邮箱",
            "is_active": "账号启用",
            "is_staff": "管理员(可访问后台)",
            "is_superuser": "超级管理员",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_superuser": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, current_user=None, target_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user = current_user
        self.target_user = target_user

        editing_self = (
            current_user is not None
            and target_user is not None
            and current_user.pk == target_user.pk
        )
        current_is_super = bool(current_user and current_user.is_superuser)

        # 保留账号 root / demo —— 用户名不可改
        if target_user is not None and target_user.username in RESERVED_USERNAMES:
            self.fields["username"].disabled = True
            self.fields["username"].help_text = "保留账号，用户名不可修改"

        # 自我保护：不能取消自己的超管/启用状态
        if editing_self:
            for fname in ("is_superuser", "is_active"):
                if fname in self.fields:
                    self.fields[fname].disabled = True
                    self.fields[fname].help_text = "不能修改自己的此项设置"

        # 管理员（非超管）越级保护：
        # 1) 不能调整任何权限相关字段（is_superuser / is_staff / is_active）
        # 2) 无法编辑超级管理员目标（视图层已拦截，这里再加一层）
        if current_user is not None and not current_is_super:
            for fname in ("is_superuser", "is_staff", "is_active"):
                if fname in self.fields:
                    self.fields[fname].disabled = True
            self.fields["is_superuser"].help_text = "仅超级管理员可调整此项"
            self.fields["is_staff"].help_text = "仅超级管理员可调整此项"
            self.fields["is_active"].help_text = "仅超级管理员可调整此项"

    def _clean_lock_field(self, field_name, original_value):
        """若字段被禁用，则强制返回原值，防止 POST 绕过。"""
        if self.fields.get(field_name) and self.fields[field_name].disabled:
            return original_value
        return self.cleaned_data.get(field_name)

    def clean_username(self):
        value = self.cleaned_data.get("username")
        if self.target_user is not None and self.target_user.username in RESERVED_USERNAMES:
            return self.target_user.username
        return value

    def clean_is_superuser(self):
        value = self.cleaned_data.get("is_superuser")
        if self.target_user is None:
            return value
        # 编辑自己：保持原值
        if self.current_user is not None and self.current_user.pk == self.target_user.pk:
            return self.target_user.is_superuser
        # 非超级管理员：保持原值
        if self.current_user is not None and not self.current_user.is_superuser:
            return self.target_user.is_superuser
        return value

    def clean_is_staff(self):
        value = self.cleaned_data.get("is_staff")
        if self.target_user is None:
            return value
        # 非超级管理员：保持原值（不能授予/撤销 staff 权限）
        if self.current_user is not None and not self.current_user.is_superuser:
            return self.target_user.is_staff
        return value

    def clean_is_active(self):
        value = self.cleaned_data.get("is_active")
        if self.target_user is None:
            return value
        # 编辑自己：保持原值
        if self.current_user is not None and self.current_user.pk == self.target_user.pk:
            return self.target_user.is_active
        # 非超级管理员：保持原值
        if self.current_user is not None and not self.current_user.is_superuser:
            return self.target_user.is_active
        return value

    def clean(self):
        cleaned = super().clean()
        # 管理员（非超管）不能编辑超级管理员
        if (
            self.current_user is not None
            and self.target_user is not None
            and not self.current_user.is_superuser
            and self.target_user.is_superuser
            and self.current_user.pk != self.target_user.pk
        ):
            raise ValidationError("你没有权限修改超级管理员账号")
        return cleaned


class AdminPasswordResetForm(forms.Form):
    """超级管理员为其他用户重置密码。"""

    new_password1 = forms.CharField(
        label="新密码",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
        help_text="留空表示不修改密码",
    )
    new_password2 = forms.CharField(
        label="确认新密码",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    def __init__(self, *args, target_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_user = target_user

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1") or ""
        p2 = cleaned.get("new_password2") or ""

        if not p1 and not p2:
            cleaned["change_password"] = False
            return cleaned

        if p1 != p2:
            self.add_error("new_password2", "两次输入的新密码不一致")

        if p1:
            try:
                validate_password(p1, user=self.target_user)
            except ValidationError as exc:
                self.add_error("new_password1", exc)

        cleaned["change_password"] = True
        return cleaned
