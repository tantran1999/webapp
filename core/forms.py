from django import forms


class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_customer_name = forms.CharField(required=True)
    shipping_phone_number = forms.CharField(required=True)
