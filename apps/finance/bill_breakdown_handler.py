from decimal import Decimal
from django.core.exceptions import ValidationError

from apps.finance.models import Charge, BillLine, BillLedger
from apps.common.utils import get_object_or_none
from apps.constants.errors.en import (
    INVALID_USER_ID,
    INVALID_PAYMENT_AMOUNT,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class BillBreakdownHandler:
    """Calculate bill breakdown and generate invoice-ready dictionary.
    
    Handles charge application (both % and INR), breakdown calculation,
    and invoice generation before transaction processing.
    """

    def __init__(
        self,
        user_id,
        subtotal,
        transaction_type="ORDER",
        reference_id=None,
        custom_charges=None,
    ) -> None:
        self.user_id = user_id
        self.subtotal = Decimal(str(subtotal))
        self.transaction_type = transaction_type
        self.reference_id = reference_id
        self.custom_charges = custom_charges or []

        # runtime objects
        self.user = None
        self.user_profile = None
        self.charges = []
        self.breakdown_lines = []
        self.total_charges = Decimal("0.00")
        self.final_amount = Decimal("0.00")
        self.bill_ledger = None
        self.invoice_dict = {}

        # validate and load
        self.__validate_amount()
        self.__get_user_info()
        self.__load_charges()

    def __validate_amount(self):
        if self.subtotal <= 0:
            raise ValidationError(INVALID_PAYMENT_AMOUNT)

    def __get_user_info(self):
        self.user = get_object_or_none(User, id=self.user_id)
        if self.user is None:
            raise ValidationError(INVALID_USER_ID)
        try:
            self.user_profile = self.user.profile
        except Exception:
            self.user_profile = None

    def __load_charges(self):
        """Load charges from database based on transaction type."""
        if self.transaction_type == "ORDER":
            self.charges = list(
                Charge.objects.filter(is_active=True, apply_to_order=True)
            )
        elif self.transaction_type == "SUBSCRIPTION":
            self.charges = list(
                Charge.objects.filter(is_active=True, apply_to_subscription=True)
            )
        else:
            self.charges = []

        # add custom charges if provided
        if self.custom_charges:
            self.charges.extend(self.custom_charges)

    def calculate_breakdown(self):
        """Calculate bill breakdown with all charges applied.
        
        Returns:
            dict: Breakdown details with lines and totals
        """
        self.breakdown_lines = []
        running_total = self.subtotal

        for charge in self.charges:
            if charge.amount_type == "%":
                # Percentage charge
                calculated = (running_total * charge.amount) / Decimal("100")
            else:
                # Fixed INR charge
                calculated = charge.amount

            line = {
                "name": charge.name,
                "description": getattr(charge, "description", ""),
                "amount_type": charge.amount_type,
                "base_amount": float(running_total if charge.amount_type == "%" else self.subtotal),
                "charge_value": float(charge.amount),
                "calculated_amount": float(calculated),
            }
            self.breakdown_lines.append(line)
            self.total_charges += calculated

        self.final_amount = self.subtotal + self.total_charges

        breakdown_dict = {
            "subtotal": float(self.subtotal),
            "lines": self.breakdown_lines,
            "total_charges": float(self.total_charges),
            "final_amount": float(self.final_amount),
        }

        return breakdown_dict

    def create_invoice_dict(self):
        """Create invoice-ready dictionary for template rendering.
        
        Returns:
            dict: Invoice data with all breakdown details
        """
        if not self.breakdown_lines:
            self.calculate_breakdown()

        customer_name = f"{self.user.first_name or ''} {self.user.last_name or ''}".strip()

        self.invoice_dict = {
            "customer_name": customer_name,
            "customer_email": self.user.email,
            "transaction_type": self.transaction_type,
            "reference_id": self.reference_id,
            "subtotal": float(self.subtotal),
            "charges": self.breakdown_lines,
            "total_charges": float(self.total_charges),
            "final_amount": float(self.final_amount),
            "currency": "INR",
        }

        return self.invoice_dict

    def save_bill_ledger(self):
        """Save breakdown to bill ledger for audit trail.
        
        Returns:
            BillLedger: Created ledger entry
        """
        if not self.breakdown_lines:
            self.calculate_breakdown()

        self.bill_ledger = BillLedger.objects.create(
            user=self.user_profile,
            transaction_type=self.transaction_type,
            reference_id=self.reference_id or "",
            subtotal=self.subtotal,
            breakdown_json={
                "subtotal": float(self.subtotal),
                "lines": self.breakdown_lines,
                "total_charges": float(self.total_charges),
                "final_amount": float(self.final_amount),
            },
            total_charges=self.total_charges,
            final_amount=self.final_amount,
        )

        return self.bill_ledger

    def get_breakdown_summary(self):
        """Get simple text summary of charges.
        
        Returns:
            str: Formatted breakdown summary
        """
        if not self.breakdown_lines:
            self.calculate_breakdown()

        lines = [f"Subtotal: ₹{self.subtotal}"]
        for line in self.breakdown_lines:
            lines.append(
                f"{line['name']}: ₹{line['calculated_amount']} ({line['amount_type']})"
            )
        lines.append(f"Total Charges: ₹{self.total_charges}")
        lines.append(f"Final Amount: ₹{self.final_amount}")

        return "\n".join(lines)
