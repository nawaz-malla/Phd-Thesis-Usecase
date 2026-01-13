# Basic Hotel Booking Smart Contract using ARC4 framework
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


class HotelBooking(ARC4Contract):
    def __init__(self) -> None:
        # --- Participants ---
        self.client = GlobalState(
            Account("NNQ4W4DT5BBTAR6JMBLWQUYVNKKKXNRBCWTMQHHNJT2PLMLP3GSVDSDEKM")
        )
        self.hotel = GlobalState(
            Account("SXPMWXP2X5TTLKTD5BN2DYXEJSN5OM6T4LNYLSHRRG56X4WD5RCVF4RC3I")
        )

        # --- Admin ---
        self.admin = GlobalState(Account)

        # --- Process Control (14 edges) ---
        self.e0 = GlobalState(UInt64(1))  # start event
        self.e1 = GlobalState(UInt64(0))  # after start xor
        self.e2 = GlobalState(UInt64(0))  # after check_room
        self.e3 = GlobalState(UInt64(0))  # after give_availability
        self.e4 = GlobalState(UInt64(0))  # after accept_booking
        self.e5 = GlobalState(UInt64(0))  # confirm=true path
        self.e6 = GlobalState(UInt64(0))  # after price_quotation
        self.e7 = GlobalState(UInt64(0))  # after confirmation
        self.e8 = GlobalState(UInt64(0))  # parallel branch 1: payment (send)
        self.e9 = GlobalState(UInt64(0))  # parallel branch 1: payment (receive)
        self.e10 = GlobalState(UInt64(0))  # parallel branch 2: booking_id (send)
        self.e11 = GlobalState(UInt64(0))  # parallel branch 2: booking_id (receive)
        self.e12 = GlobalState(UInt64(0))  # after parallel join
        self.e13 = GlobalState(UInt64(0))  # cancel=true path
        self.e15 = GlobalState(UInt64(0))  # reject path

        self.locked = GlobalState(UInt64(0))

        # --- Data Objects ---
        self.booking_date = GlobalState(String(""))
        self.num_rooms = GlobalState(UInt64(0))
        self.room_available = GlobalState(UInt64(0))
        self.confirm_flag = GlobalState(UInt64(0))
        self.quotation = GlobalState(String(""))
        self.payment_address = GlobalState(String(""))
        self.payment_completed = GlobalState(UInt64(0))
        self.booking_id = GlobalState(String(""))
        self.cancel_flag = GlobalState(UInt64(0))
        self.cancel_motivation = GlobalState(String(""))

    @baremethod(create="allow")
    def create(self) -> None:
        self.admin.value = Txn.sender
        self.e0.value = UInt64(1)
        self.locked.value = UInt64(0)
        log(Bytes(b"HotelBooking deployed"))

    # ========== SUBROUTINES (diagram flow order) ==========

    @subroutine
    def start_event(self) -> UInt64:
        """Start event"""
        if self.e0.value > UInt64(0):
            self.e0.value -= UInt64(1)
            self.e1.value += UInt64(1)
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def xor_start(self) -> UInt64:
        """XOR gateway: start"""
        if self.e1.value > UInt64(0):
            self.e1.value -= UInt64(1)
            self.e2.value += UInt64(1)
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def xor1_accept_booking(self) -> UInt64:
        """XOR gateway 1: confirm check after accept_booking"""
        if self.e4.value > UInt64(0):
            self.e4.value -= UInt64(1)
            if self.confirm_flag.value == UInt64(0):
                self.e1.value += UInt64(1)
                log(Bytes(b"XOR1: confirm=false -> loop back"))
            else:
                self.e5.value += UInt64(1)
                log(Bytes(b"XOR1: confirm=true -> continue"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def xor2_confirmation(self) -> UInt64:
        """XOR gateway 2: confirm check after confirmation"""
        if self.e7.value > UInt64(0):
            self.e7.value -= UInt64(1)
            if self.confirm_flag.value == UInt64(0):
                self.e13.value += UInt64(1)
                log(Bytes(b"XOR2: confirm=false -> reject"))
            else:
                # Parallel split
                self.e8.value += UInt64(1)
                self.e10.value += UInt64(1)
                log(Bytes(b"XOR2: confirm=true -> parallel split"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def parallel_join(self) -> UInt64:
        """Parallel gateway: join payment and booking branches"""
        if self.e9.value > UInt64(0) and self.e11.value > UInt64(0):
            self.e9.value -= UInt64(1)
            self.e11.value -= UInt64(1)
            self.e12.value += UInt64(1)
            log(Bytes(b"Parallel join: both branches complete"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def end_success(self) -> UInt64:
        """End event: success"""
        if self.e12.value > UInt64(0):
            self.e12.value -= UInt64(1)
            log(Bytes(b"Process completed: success"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def end_reject(self) -> UInt64:
        """End event: reject"""
        if self.e15.value > UInt64(0):
            self.e15.value -= UInt64(1)
            log(Bytes(b"Process completed: reject"))
            return UInt64(1)
        return UInt64(0)

    # ========== EXECUTION ENGINE ==========

    @subroutine
    def execute_one_rule(self) -> UInt64:
        if self.start_event() != UInt64(0):
            return UInt64(1)
        if self.xor_start() != UInt64(0):
            return UInt64(1)
        if self.xor1_accept_booking() != UInt64(0):
            return UInt64(1)
        if self.xor2_confirmation() != UInt64(0):
            return UInt64(1)
        if self.parallel_join() != UInt64(0):
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
            + self.e15.value
        )

        if total_tokens > UInt64(0):
            log(Bytes(b"The process instance is RUNNING"))
        else:
            log(Bytes(b"The process instance is COMPLETED"))
        return UInt64(1)

    # ========== TASKS (diagram flow order: left to right, top to bottom) ==========

    # --- Top Flow: Availability Loop ---
    @abimethod
    def check_room(self, date: String, num_rooms: UInt64) -> None:
        """Task 1: Client checks room"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e2.value > UInt64(0), "Task not active"
        assert Txn.sender == self.client.value, "Only client"

        self.e2.value -= UInt64(1)
        self.booking_date.value = date
        self.num_rooms.value = num_rooms
        self.e3.value += UInt64(1)
        log(Bytes(b"Client: check_room"))

    @abimethod
    def give_availability(self, confirm: UInt64) -> None:
        """Task 2: Hotel gives availability"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e3.value > UInt64(0), "Task not active"
        assert Txn.sender == self.hotel.value, "Only hotel"

        self.e3.value -= UInt64(1)
        self.room_available.value = confirm
        self.e4.value += UInt64(1)
        log(Bytes(b"Hotel: give_availability"))

    @abimethod
    def accept_booking(self, confirm: UInt64) -> None:
        """Task 3: Client accepts booking"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e4.value > UInt64(0), "Task not active"
        assert Txn.sender == self.client.value, "Only client"

        self.confirm_flag.value = confirm
        log(Bytes(b"Client: accept_booking"))
        self.execute()

    # --- Middle Flow: Price & Confirmation ---
    @abimethod
    def price_quotation(self, quotation: String) -> None:
        """Task 4: Hotel sends price quotation"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e5.value > UInt64(0), "Task not active"
        assert Txn.sender == self.hotel.value, "Only hotel"

        self.e5.value -= UInt64(1)
        self.quotation.value = quotation
        self.e6.value += UInt64(1)
        log(Bytes(b"Hotel: price_quotation"))

    @abimethod
    def confirmation(self, confirm: UInt64, book_room: UInt64) -> None:
        """Task 5: Client confirms booking"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e6.value > UInt64(0), "Task not active"
        assert Txn.sender == self.client.value, "Only client"

        self.e6.value -= UInt64(1)
        self.confirm_flag.value = confirm
        self.e7.value += UInt64(1)
        log(Bytes(b"Client: confirmation"))
        self.execute()

    # --- Parallel Flow: Payment Branch ---
    @abimethod
    def payment_send(self, address_payable: String) -> None:
        """Task 6: Client sends payment address"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e8.value > UInt64(0), "Task not active"
        assert Txn.sender == self.client.value, "Only client"

        self.e8.value -= UInt64(1)
        self.payment_address.value = address_payable
        self.e9.value += UInt64(1)
        log(Bytes(b"Client: payment_send"))
        self.execute()

    @abimethod
    def accept_payment(self, address_payable: String) -> None:
        """Task 7: Hotel receives payment"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e9.value > UInt64(0), "Task not active"
        assert Txn.sender == self.hotel.value, "Only hotel"

        itxn.Payment(
            amount=10000,
            receiver=self.hotel.value,
            fee=2500,
        ).submit()

        self.payment_completed.value = UInt64(1)
        log(Bytes(b"Hotel: accept_payment"))
        self.execute()

    # --- Parallel Flow: Booking Confirmation Branch ---
    @abimethod
    def give_id(self, booking_id: String) -> None:
        """Task 8: Client sends booking ID"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e10.value > UInt64(0), "Task not active"
        assert Txn.sender == self.client.value, "Only client"

        self.e10.value -= UInt64(1)
        self.booking_id.value = booking_id
        self.e11.value += UInt64(1)
        log(Bytes(b"Client: give_id"))
        # self.execute()

    @abimethod
    def booking_confirmation(self, cancel: UInt64) -> None:
        """Task 9: Hotel confirms booking"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e11.value > UInt64(0), "Task not active"
        assert Txn.sender == self.hotel.value, "Only hotel"

        self.cancel_flag.value = cancel
        log(Bytes(b"Hotel: booking_confirmation"))
        self.execute()

    # --- Cancel/Refund Flow ---
    @abimethod
    def cancel_order(self, motivation: String) -> None:
        """Task 10: Client cancels order"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert Txn.sender == self.client.value, "Only client"
        assert self.e13.value > UInt64(0), "Task not active"

        self.cancel_motivation.value = motivation
        self.cancel_flag.value = UInt64(1)
        log(Bytes(b"Client: cancel_order"))

    # --- Reject Flow ---
    @abimethod
    def reject_order(self) -> None:
        """Task 13: Client rejects order"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e15.value > UInt64(0), "Task not active"
        assert Txn.sender == self.client.value, "Only client"

        log(Bytes(b"Client: reject_order"))
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
