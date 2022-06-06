from django.contrib import admin

from .models import *


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user',
                    'ordered',
                    'being_delivered',
                    'received',
                    'shipping_address',
                    ]
    list_display_links = [
        'user',
        'shipping_address',
    ]
    list_filter = ['ordered',
                   'being_delivered',
                   'received', ]
    search_fields = [
        'user__username',
        'ref_code'
    ]


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'customer_name',
        'phone_number',
    ]
    search_fields = ['user', 'street_address', 'apartment_address']


admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(UserProfile)
