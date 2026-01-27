# Fixed Updated Version of BikeRental contract with give_credits and give_receipt
from algopy import (
    Account,
    Bytes,
    GlobalState,
    String,
    UInt64,
    Txn,
    itxn,
    log,
    subroutine,
)
from algopy.arc4 import ARC4Contract, abimethod, baremethod


class BikeRental(ARC4Contract):
    def __init__(self) -> None:
        # --- Participants ---
        self.customer = GlobalState(
            Account("GPG6DUODJFQ4TQTECLCI36JMBKOXOKY56HZSNQ6PQTLTOI4XFWHSNPK4LQ")
        )
        self.bike_center = GlobalState(
            Account("R7R7MB4X6DC33BXAR5OKBTRMBLKO6JGDTSCBEHH523T2XGMCFW3JRN3D2M")
        )
        self.insurer = GlobalState(
            Account("R7R7MB4X6DC33BXAR5OKBTRMBLKO6JGDTSCBEHH523T2XGMCFW3JRN3D2M")
        )

        # --- Admin ---
        self.admin = GlobalState(Account)

        # --- Process Control Edges ---
        self.e0 = GlobalState(UInt64(1))  # start event
        self.e1 = GlobalState(UInt64(0))  # after request_availability
        self.e2 = GlobalState(UInt64(0))  # after give_availability
        self.e3 = GlobalState(UInt64(0))  # isAvailable==true path
        self.e4 = GlobalState(UInt64(0))  # isAvailable==false path (end reject)
        self.e5 = GlobalState(UInt64(0))  # after request_insurance
        self.e6 = GlobalState(UInt64(0))  # after estimate_insurance_cost
        self.e7 = GlobalState(UInt64(0))  # insuranceReq==false path
        self.e8 = GlobalState(UInt64(0))  # insuranceReq==true path
        self.e9 = GlobalState(UInt64(0))  # after pay_insurance
        self.e10 = GlobalState(UInt64(0))  # after insurance confirmation from insurer
        self.e11 = GlobalState(UInt64(0))  # after XOR join (insurance paths)
        self.e12 = GlobalState(UInt64(0))  # after pay_bike
        self.e13 = GlobalState(UInt64(0))  # after voucher
        self.e14 = GlobalState(UInt64(0))  # after give_bike
        self.e15 = GlobalState(UInt64(0))  # after report_damage
        self.e16 = GlobalState(UInt64(0))  # after damage_evaluation
        self.e17 = GlobalState(UInt64(0))  # ask==true path (refund requested)
        self.e18 = GlobalState(UInt64(0))  # ask==false path (no refund)
        self.e19 = GlobalState(UInt64(0))  # after damage_refund payment
        self.e20 = GlobalState(UInt64(0))  # after XOR join (refund paths)
        self.e21 = GlobalState(UInt64(0))  # after give_feedback
        self.e22 = GlobalState(UInt64(0))  # after give_bike_back
        self.e23 = GlobalState(UInt64(0))  # after give_credits

        self.locked = GlobalState(UInt64(0))

        # --- Data Objects ---
        self.bike_type = GlobalState(String(""))
        self.is_available = GlobalState(UInt64(0))
        self.bike_cost = GlobalState(UInt64(0))
        self.insurance_requested = GlobalState(UInt64(0))
        self.insurance_cost = GlobalState(UInt64(0))
        self.insurance_data = GlobalState(String(""))
        self.voucher_data = GlobalState(String(""))
        self.bike_id = GlobalState(String(""))
        self.damage_description = GlobalState(String(""))
        self.refund_requested = GlobalState(UInt64(0))
        self.refund_amount = GlobalState(UInt64(0))
        self.feedback_data = GlobalState(String(""))
        self.voucher_id = GlobalState(String(""))
        self.credits_amount = GlobalState(UInt64(0))
        self.receipt_data = GlobalState(String(""))

    @baremethod(create="allow")
    def create(self) -> None:
        self.admin.value = Txn.sender
        self.e0.value = UInt64(1)
        self.locked.value = UInt64(0)
        log(Bytes(b"BikeRental deployed"))

    # ========== SUBROUTINES (process flow) ==========

    @subroutine
    def start_event(self) -> UInt64:
        """Start event"""
        if self.e0.value > UInt64(0):
            self.e0.value -= UInt64(1)
            self.e1.value += UInt64(1)
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def xor1_availability_check(self) -> UInt64:
        """XOR gateway 1: Check if bike is available"""
        if self.e2.value > UInt64(0):
            self.e2.value -= UInt64(1)
            if self.is_available.value == UInt64(0):
                self.e4.value += UInt64(1)
                log(Bytes(b"XOR1: isAvailable==false -> end reject"))
            else:
                self.e3.value += UInt64(1)
                log(Bytes(b"XOR1: isAvailable==true -> continue"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def xor2_insurance_check(self) -> UInt64:
        """XOR gateway 2: Check if insurance is requested"""
        if self.e6.value > UInt64(0):
            self.e6.value -= UInt64(1)
            if self.insurance_requested.value == UInt64(0):
                self.e7.value += UInt64(1)
                log(Bytes(b"XOR2: insuranceReq==false -> skip insurance"))
            else:
                self.e8.value += UInt64(1)
                log(Bytes(b"XOR2: insuranceReq==true -> pay insurance"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def xor3_insurance_join(self) -> UInt64:
        """XOR gateway 3: Join insurance paths"""
        if self.e7.value > UInt64(0):
            self.e7.value -= UInt64(1)
            self.e11.value += UInt64(1)
            log(Bytes(b"XOR3: no insurance path joined"))
            return UInt64(1)
        if self.e10.value > UInt64(0):
            self.e10.value -= UInt64(1)
            self.e11.value += UInt64(1)
            log(Bytes(b"XOR3: insurance path joined"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def xor4_refund_check(self) -> UInt64:
        """XOR gateway 4: Check if refund is requested"""
        if self.e16.value > UInt64(0):
            self.e16.value -= UInt64(1)
            if self.refund_requested.value == UInt64(1):
                self.e17.value += UInt64(1)
                log(Bytes(b"XOR4: ask==true -> process refund"))
            else:
                self.e18.value += UInt64(1)
                log(Bytes(b"XOR4: ask==false -> skip refund"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def xor5_refund_join(self) -> UInt64:
        """XOR gateway 5: Join refund paths"""
        if self.e18.value > UInt64(0):
            self.e18.value -= UInt64(1)
            self.e20.value += UInt64(1)
            log(Bytes(b"XOR5: no refund path joined"))
            return UInt64(1)
        if self.e19.value > UInt64(0):
            self.e19.value -= UInt64(1)
            self.e20.value += UInt64(1)
            log(Bytes(b"XOR5: refund path joined"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def end_success(self) -> UInt64:
        """End event: success (after give_receipt)"""
        if self.e23.value > UInt64(0):
            self.e23.value -= UInt64(1)
            log(Bytes(b"Process completed: success"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def end_reject(self) -> UInt64:
        """End event: reject (bike not available)"""
        if self.e4.value > UInt64(0):
            self.e4.value -= UInt64(1)
            log(Bytes(b"Process completed: reject - bike not available"))
            return UInt64(1)
        return UInt64(0)

    # ========== EXECUTION ENGINE ==========

    @subroutine
    def execute_one_rule(self) -> UInt64:
        if self.start_event() != UInt64(0):
            return UInt64(1)
        if self.xor1_availability_check() != UInt64(0):
            return UInt64(1)
        if self.xor2_insurance_check() != UInt64(0):
            return UInt64(1)
        if self.xor3_insurance_join() != UInt64(0):
            return UInt64(1)
        if self.xor4_refund_check() != UInt64(0):
            return UInt64(1)
        if self.xor5_refund_join() != UInt64(0):
            return UInt64(1)
        if self.end_success() != UInt64(0):
            return UInt64(1)
        if self.end_reject() != UInt64(0):
            return UInt64(1)
        return UInt64(0)

    @abimethod
    def execute(self) -> UInt64:
        assert self.locked.value == UInt64(0), "Contract is locked"
        executed = True
        while executed:
            rule_executed = self.execute_one_rule()
            executed = rule_executed != UInt64(0)

        total_tokens = (
            self.e0.value
            + self.e1.value
            + self.e2.value
            + self.e3.value
            + self.e4.value
            + self.e5.value
            + self.e6.value
            + self.e7.value
            + self.e8.value
            + self.e9.value
            + self.e10.value
            + self.e11.value
            + self.e12.value
            + self.e13.value
            + self.e14.value
            + self.e15.value
            + self.e16.value
            + self.e17.value
            + self.e18.value
            + self.e19.value
            + self.e20.value
            + self.e21.value
            + self.e22.value
            + self.e23.value
        )

        if total_tokens > UInt64(0):
            log(Bytes(b"The process instance is RUNNING"))
        else:
            log(Bytes(b"The process instance is COMPLETED"))
        return UInt64(1)

    # ========== TASKS ==========

    # --- Initial Flow: Availability Check ---
    @abimethod
    def request_availability(self, bike_type: String) -> None:
        """Task 1: Customer requests availability"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e1.value > UInt64(0), "Task not active"
        assert Txn.sender == self.customer.value, "Only customer"

        self.e1.value -= UInt64(1)
        self.bike_type.value = bike_type
        self.e2.value += UInt64(1)
        log(Bytes(b"Customer: request_availability"))

    @abimethod
    def give_availability(self, is_available: UInt64, cost: UInt64) -> None:
        """Task 2: Bike center gives availability"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e2.value > UInt64(0), "Task not active"
        assert Txn.sender == self.bike_center.value, "Only bike center"

        self.is_available.value = is_available
        self.bike_cost.value = cost
        log(Bytes(b"BikeCenter: give_availability"))
        self.execute()

    # --- Insurance Flow ---
    @abimethod
    def request_insurance(self, insurance_req: UInt64) -> None:
        """Task 3: Customer requests insurance"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e3.value > UInt64(0), "Task not active"
        assert Txn.sender == self.customer.value, "Only customer"

        self.e3.value -= UInt64(1)
        self.insurance_requested.value = insurance_req
        self.e5.value += UInt64(1)
        log(Bytes(b"Customer: request_insurance"))

    @abimethod
    def estimate_insurance_cost(self, insurance_cost: UInt64) -> None:
        """Task 4: Bike center estimates insurance cost"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e5.value > UInt64(0), "Task not active"
        assert Txn.sender == self.bike_center.value, "Only bike center"

        self.e5.value -= UInt64(1)
        self.insurance_cost.value = insurance_cost
        self.e6.value += UInt64(1)
        log(Bytes(b"BikeCenter: estimate_insurance_cost"))
        self.execute()

    @abimethod
    def pay_insurance(self) -> None:
        """Task 5: Customer pays insurance"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e8.value > UInt64(0), "Task not active"
        assert Txn.sender == self.customer.value, "Only customer"

        self.e8.value -= UInt64(1)

        # Payment to bike center for insurance
        itxn.Payment(
            amount=self.insurance_cost.value,
            receiver=self.bike_center.value,
            fee=1000,
        ).submit()

        self.e9.value += UInt64(1)
        log(Bytes(b"Customer: pay_insurance"))

    @abimethod
    def confirm_insurance(self, insurance_data: String) -> None:
        """Task 6: Insurer confirms insurance"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e9.value > UInt64(0), "Task not active"
        assert Txn.sender == self.insurer.value, "Only insurer"

        self.e9.value -= UInt64(1)
        self.insurance_data.value = insurance_data
        self.e10.value += UInt64(1)
        log(Bytes(b"Insurer: confirm_insurance"))
        self.execute()

    # --- Payment and Bike Delivery Flow ---
    @abimethod
    def pay_bike(self) -> None:
        """Task 7: Customer pays for bike"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e11.value > UInt64(0), "Task not active"
        assert Txn.sender == self.customer.value, "Only customer"

        self.e11.value -= UInt64(1)

        # Payment to bike center for bike rental
        itxn.Payment(
            amount=self.bike_cost.value,
            receiver=self.bike_center.value,
            fee=1000,
        ).submit()

        self.e12.value += UInt64(1)
        log(Bytes(b"Customer: pay_bike"))

    @abimethod
    def provide_voucher(self, voucher_data: String) -> None:
        """Task 8: Bike center provides voucher"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e12.value > UInt64(0), "Task not active"
        assert Txn.sender == self.bike_center.value, "Only bike center"

        self.e12.value -= UInt64(1)
        self.voucher_data.value = voucher_data
        self.e13.value += UInt64(1)
        log(Bytes(b"BikeCenter: provide_voucher"))

    @abimethod
    def give_bike(self, bike_id: String) -> None:
        """Task 9: Bike center gives bike"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e13.value > UInt64(0), "Task not active"
        assert Txn.sender == self.bike_center.value, "Only bike center"

        self.e13.value -= UInt64(1)
        self.bike_id.value = bike_id
        self.e14.value += UInt64(1)
        log(Bytes(b"BikeCenter: give_bike"))

    # --- Damage Reporting Flow ---
    @abimethod
    def report_damage(self, description: String) -> None:
        """Task 10: Customer reports damage"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e14.value > UInt64(0), "Task not active"
        assert Txn.sender == self.customer.value, "Only customer"

        self.e14.value -= UInt64(1)
        self.damage_description.value = description
        self.e15.value += UInt64(1)
        log(Bytes(b"Customer: report_damage"))

    @abimethod
    def damage_evaluation(self, ask_refund: UInt64, amount: UInt64) -> None:
        """Task 11: Bike center evaluates damage"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e15.value > UInt64(0), "Task not active"
        assert Txn.sender == self.bike_center.value, "Only bike center"

        self.e15.value -= UInt64(1)
        self.refund_requested.value = ask_refund
        self.refund_amount.value = amount
        self.e16.value += UInt64(1)
        log(Bytes(b"BikeCenter: damage_evaluation"))
        self.execute()

    @abimethod
    def damage_refund(self) -> None:
        """Task 12: Customer pays damage refund"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e17.value > UInt64(0), "Task not active"
        assert Txn.sender == self.customer.value, "Only customer"

        self.e17.value -= UInt64(1)

        # Payment for damages
        itxn.Payment(
            amount=self.refund_amount.value,
            receiver=self.bike_center.value,
            fee=1000,
        ).submit()

        self.e19.value += UInt64(1)
        log(Bytes(b"Customer: damage_refund"))
        self.execute()

    # --- Final Flow: Feedback and Return ---
    @abimethod
    def give_feedback(self, feedback: String) -> None:
        """Task 13: Customer gives feedback"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e20.value > UInt64(0), "Task not active"
        assert Txn.sender == self.customer.value, "Only customer"

        self.e20.value -= UInt64(1)
        self.feedback_data.value = feedback
        self.e21.value += UInt64(1)
        log(Bytes(b"Customer: give_feedback"))

    @abimethod
    def give_bike_back(self, voucher_id: String, bike_id: String) -> None:
        """Task 14: Customer returns bike"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e21.value > UInt64(0), "Task not active"
        assert Txn.sender == self.customer.value, "Only customer"

        self.e21.value -= UInt64(1)
        self.voucher_id.value = voucher_id
        # Verify bike_id matches
        assert bike_id == self.bike_id.value, "Bike ID mismatch"

        self.e22.value += UInt64(1)
        log(Bytes(b"Customer: give_bike_back"))

    @abimethod
    def give_credits(self, credits: UInt64) -> None:
        """Task 15: Bike center gives credits"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e22.value > UInt64(0), "Task not active"
        assert Txn.sender == self.bike_center.value, "Only bike center"

        self.e22.value -= UInt64(1)
        self.credits_amount.value = credits
        self.e23.value += UInt64(1)
        log(Bytes(b"BikeCenter: give_credits"))

    @abimethod
    def give_receipt(self, data: String) -> None:
        """Task 16: Bike center gives receipt"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e23.value > UInt64(0), "Task not active"
        assert Txn.sender == self.bike_center.value, "Only bike center"

        self.e23.value -= UInt64(1)
        self.receipt_data.value = data
        log(Bytes(b"BikeCenter: give_receipt"))
        self.execute()

    # ========== ADMIN FUNCTIONS ==========

    @baremethod(allow_actions=["UpdateApplication"])
    def update(self) -> None:
        assert Txn.sender == self.admin.value, "Only admin can update"
        self.locked.value = UInt64(1)
        log(Bytes(b"Contract locked for update"))

    @abimethod
    def unlock(self) -> None:
        assert Txn.sender == self.admin.value, "Only admin can unlock"
        self.locked.value = UInt64(0)
        log(Bytes(b"Contract unlocked"))

    @abimethod(allow_actions=["DeleteApplication"])
    def delete(self) -> None:
        assert Txn.sender == self.admin.value, "Only admin can delete"
        assert self.locked.value == UInt64(0), "Contract is locked"
        log(Bytes(b"Contract deleted successfully"))
