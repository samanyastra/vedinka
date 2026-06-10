from datetime import date
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError

from apps.common.utils import get_object_or_none, create_rand_string
from apps.common.models import TransactionStatus
from apps.finance.models import Order, Payment
from apps.constants.errors.en import (
    INVALID_USER_ID,
    LOCAL_ORDER_NOT_PREPARED,
    INVALID_TRANSACTION_DATA,
    GATEWAY_VERIFICATION_NOT_SUPPORTED,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class TransactionHandler:
    """Central transaction helper for gateway-integrated order creation.

    This class is gateway-agnostic: pass a gateway client instance (for
    example a Razorpay client) via `client`. If not provided it will try
    to use `settings.RAZ_CLIENT` and `settings.RAZORPAY_KEY`.
    """

    def __init__(
        self,
        user_id,
        transaction_amount,
        actual_amount=None,
        payment=None,
        *,
        client=None,
        client_public_key=None,
        gateway="razorpay",
    ) -> None:
        self.client = client or getattr(settings, "RAZ_CLIENT", None)
        self.client_public_key = client_public_key or getattr(
            settings, "RAZORPAY_KEY_ID", None
        )
        self.gateway = gateway

        self.user_id = user_id
        self.transaction_amount = transaction_amount
        self.actual_amount = (
            transaction_amount if actual_amount is None else actual_amount
        )

        # runtime objects
        self.order: Order | None = None
        self.payment: Payment | None = payment
        self.order_payload: dict = {}
        self.user_prefill_info: None | dict = None
        self.checkout_data: dict | None = None

        # load user and prepare local records
        self.__get_user_info()
        self.__prepare_transaction()
        self.make_order_payload()

    def __get_user_info(self):
        self.user = get_object_or_none(User, id=self.user_id)
        if self.user is None:
            raise ValidationError(INVALID_USER_ID)
        # prefer the UserProfile for relations used by finance models
        try:
            self.user_profile = self.user.profile
        except Exception:
            self.user_profile = None
        return self.user

    def __prepare_transaction(self):
        # ensure a TransactionStatus exists for pending
        pending_status, _ = TransactionStatus.objects.get_or_create(name="PENDING")
        self.pending_status = pending_status

        if self.payment is None:
            # create an Order and a Payment placeholder locally
            local_order_id = create_rand_string(24)
            self.order = Order.objects.create(
                local_order_id=local_order_id,
                user=self.user_profile,
                transaction_status=self.pending_status,
                amount=self.transaction_amount,
                order_date=date.today(),
            )

            self.payment = Payment.objects.create(
                order=self.order,
                gateway=self.gateway,
                gateway_payment_id="",
                gateway_order_id="",
                status="PENDING",
                amount=self.transaction_amount,
                raw_response={},
            )
            return self.payment

        # if payment was provided, try to set related order
        if self.payment and not self.payment.order:
            # create a minimal order
            local_order_id = create_rand_string(24)
            self.order = Order.objects.create(
                local_order_id=local_order_id,
                user=self.user_profile,
                transaction_status=self.pending_status,
                amount=self.transaction_amount,
                order_date=date.today(),
            )
            self.payment.order = self.order
            self.payment.save()

        return self.payment

    def make_order_payload(self):
        self.order_amount = self.inr_to_paise(self.transaction_amount)
        self.order_payload = {
            "amount": self.order_amount,
            "currency": "INR",
            "receipt": (
                str(self.order.local_order_id) if self.order else str(uuid.uuid4())
            ),
        }
        return self.order_payload

    def create_remote_transaction(self):
        if self.order is None:
            raise ValidationError(LOCAL_ORDER_NOT_PREPARED)

        if self.order.client_order_id:
            # remote order already created
            return {"id": self.order.client_order_id}

        if not self.client:
            raise RuntimeError("Gateway client not configured")

        try:
            remote_order = self.client.order.create(self.order_payload)
            # store gateway reference on Order and Payment
            remote_id = (
                remote_order.get("id")
                if isinstance(remote_order, dict)
                else getattr(remote_order, "id", None)
            )
            if remote_id:
                self.order.client_order_id = remote_id
                self.order.save()

                self.payment.gateway_order_id = remote_id
                self.payment.raw_response = remote_order
                self.payment.save()

            return remote_order
        except Exception as e:
            raise Exception(str(e))

    def inr_to_paise(self, value):
        value = int(round(value))
        return value * 100

    def make_user_prefill_information(self):
        if self.user_prefill_info is None:
            self.create_remote_transaction()
            name = f"{self.user.first_name or ''} {self.user.last_name or ''}".strip()
            contact = None
            if hasattr(self, "user_profile") and self.user_profile:
                contact = getattr(self.user_profile, "phone_number", None)

            self.user_prefill_info = {
                "key": self.client_public_key,
                "prefill": {
                    "name": name,
                    "email": self.user.email,
                    "contact": contact,
                },
                "amount": self.order_amount,
                "currency": "INR",
                "name": getattr(settings, "COMPANY_NAME", "Vedinka"),
                "order_id": self.order.client_order_id,
                "config": self.config,
                "transaction_id": str(self.payment.id),
            }
            return self.user_prefill_info
        return self.user_prefill_info

    def verify_transaction(self, checkout_data):
        # Basic validation of input keys
        required = {"razorpay_order_id", "razorpay_payment_id", "razorpay_signature"}
        if not required.issubset(set(checkout_data.keys())):
            raise ValidationError(INVALID_TRANSACTION_DATA)

        self.checkout_data = checkout_data

        if not self.client or not hasattr(
            self.client.utility, "verify_payment_signature"
        ):
            raise RuntimeError(GATEWAY_VERIFICATION_NOT_SUPPORTED)

        status = self.client.utility.verify_payment_signature(self.checkout_data)
        return status

    def complete_transaction(self):
        # mark payment and order as completed
        complete_status, _ = TransactionStatus.objects.get_or_create(name="SUCCESS")

        self.payment.status = "SUCCESS"
        self.payment.gateway_payment_id = self.checkout_data.get("razorpay_payment_id")
        self.payment.gateway_order_id = self.checkout_data.get("razorpay_order_id")
        # include the signature/payment payload
        self.payment.raw_response = {
            **(self.payment.raw_response or {}),
            **self.checkout_data,
        }
        self.payment.save()

        if self.order:
            self.order.transaction_status = complete_status
            self.order.client_order_id = (
                self.payment.gateway_order_id or self.order.client_order_id
            )
            self.order.save()

        return self.payment

    @property
    def config(self):
        return {
            "display": {
                "hide": [{"method": "upi", "flows": ["qr"]}],
                "preferences": {"show_default_blocks": True},
            }
        }
