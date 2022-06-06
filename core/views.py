import random
import string
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, View

from .forms import CheckoutForm
from .models import *

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'order': order,
            }
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "Bạn chưa có đơn hàng nào")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                print("User is entering a new shipping address")
                shipping_address1 = form.cleaned_data.get(
                    'shipping_address')
                shipping_address2 = form.cleaned_data.get(
                    'shipping_address2')
                shipping_customer_name = form.cleaned_data.get(
                    'shipping_customer_name')
                shipping_phone_number = form.cleaned_data.get(
                    'shipping_phone_number')

                if is_valid_form([shipping_address1, shipping_customer_name, shipping_phone_number]):
                    shipping_address = Address(
                        user=self.request.user,
                        street_address=shipping_address1,
                        apartment_address=shipping_address2,
                        customer_name=shipping_customer_name,
                        phone_number=shipping_phone_number,
                    )
                    shipping_address.save()

                    order.shipping_address = shipping_address
                    order_items = order.items.all()
                    order_items.update(ordered=True)
                    for item in order_items:
                        item.save()
                    order.ordered = True
                    order.save()
                    messages.success(
                        self.request, "Your order was successful!")
                    return redirect("core:home")

                else:
                    messages.info(
                        self.request, "Vui lòng điền đầy đủ thông tin nhận hàng")
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")


class HomeView(ListView):
    model = Item
    paginate_by = 12
    template_name = "home.html"


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "Bạn chưa có đơn hàng nào")
            return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "Sản phẩm đã được thêm vào giỏ hàng")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "Sản phẩm đã được thêm vào giỏ hàng")
        return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "Sản phẩm đã được xóa khỏi giỏ hàng")
            return redirect("core:order-summary")
        else:
            messages.info(request, "Sản phẩm chưa được thêm vào giỏ hàng")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "Bạn chưa có đơn hàng nào")


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            return redirect("core:order-summary")
        else:
            messages.info(request, "Sản phẩm chưa được thêm vào giỏ hàng")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "Bạn chưa có đơn hàng nào")
        return redirect("core:product", slug=slug)
