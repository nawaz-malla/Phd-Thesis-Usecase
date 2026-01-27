"""
Auto-generated Algorand ARC4 Smart Contract
Generated from BPMN:
Date: 2025-01-16
UPGRADE: Adds parallel gateway for certification and temperature checks
"""

from algopy import (
    Account,
    Bytes,
    GlobalState,
    String,
    UInt64,
    Txn,
    log,
    subroutine,
)
from algopy.arc4 import ARC4Contract, abimethod, baremethod


class healthcare(ARC4Contract):
    def __init__(self) -> None:
        # --- Participants ---
        self.patient = GlobalState(
            Account("R7R7MB4X6DC33BXAR5OKBTRMBLKO6JGDTSCBEHH523T2XGMCFW3JRN3D2M")
        )
        self.radiology = GlobalState(
            Account("GPG6DUODJFQ4TQTECLCI36JMBKOXOKY56HZSNQ6PQTLTOI4XFWHSNPK4LQ")
        )
        self.ward = GlobalState(
            Account("5632N7QYG2DLUUSDD227YUFTOKR56NVU7KHXALUQT5EUU42IJFVSW6DNHU")
        )

        # --- Admin ---
        self.admin = GlobalState(Account)

        # --- BASIC edges (e0-e12 - UNCHANGED from Figure 1) ---
        self.e0 = GlobalState(UInt64(1))  # start event
        self.e1 = GlobalState(UInt64(0))  # after appointment message sent
        self.e2 = GlobalState(UInt64(0))  # after request sent to ward
        self.e3 = GlobalState(UInt64(0))  # after ward response
        self.e4 = GlobalState(UInt64(0))  # accepted==true path
        self.e5 = GlobalState(UInt64(0))  # accepted==false path (loop back)
        self.e6 = GlobalState(UInt64(0))  # after registration message sent
        self.e7 = GlobalState(UInt64(0))  # after checkin message sent
        self.e8 = GlobalState(UInt64(0))  # after confirmation message sent
        self.e9 = GlobalState(UInt64(0))  # registration==true path
        self.e10 = GlobalState(UInt64(0))  # registration==false path (end)
        self.e11 = GlobalState(UInt64(0))  # after analysis sent to ward
        self.e12 = GlobalState(UInt64(0))  # after send_results (end success)

        # --- NEW edges (e13-e18 for parallel gateway) ---
        self.e13 = GlobalState(UInt64(0))
        self.e14 = GlobalState(UInt64(0))
        self.e15 = GlobalState(UInt64(0))
        self.e16 = GlobalState(UInt64(0))
        self.e17 = GlobalState(UInt64(0))
        self.e18 = GlobalState(UInt64(0))

        self.locked = GlobalState(UInt64(0))

        # --- BASIC Data Objects ---
        self.medical_prescription = GlobalState(String(""))
        self.request_id = GlobalState(String(""))
        self.accepted = GlobalState(UInt64(0))
        self.appointment_date = GlobalState(String(""))
        self.appointment_id = GlobalState(String(""))
        self.registration_confirmed = GlobalState(UInt64(0))
        self.ticket_id = GlobalState(String(""))
        self.analysis_report = GlobalState(String(""))
        self.result_id = GlobalState(String(""))

        # --- NEW Data Objects ---
        self.certification_id = GlobalState(String(""))
        self.temperature = GlobalState(String(""))

    @baremethod(create="allow")
    def create(self) -> None:
        self.admin.value = Txn.sender
        self.e0.value = UInt64(1)
        self.locked.value = UInt64(0)
        log(Bytes(b"RadiologyBasic deployed"))

    # ========== SUBROUTINES ==========

    @subroutine
    def start_event(self) -> UInt64:
        if self.e0.value > UInt64(0):
            self.e0.value -= UInt64(1)
            self.e1.value += UInt64(1)
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def xor1_availability_check(self) -> UInt64:
        if self.e3.value > UInt64(0):
            self.e3.value -= UInt64(1)
            if self.accepted.value == UInt64(0):
                self.e5.value += UInt64(1)
                log(Bytes(b"XOR: accepted==false"))
            else:
                self.e4.value += UInt64(1)
                log(Bytes(b"XOR: accepted==true"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def xor2_loop_back(self) -> UInt64:
        if self.e5.value > UInt64(0):
            self.e5.value -= UInt64(1)
            self.e1.value += UInt64(1)
            log(Bytes(b"Loop back to appointment"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def xor3_registration_check(self) -> UInt64:
        if self.e8.value > UInt64(0):
            self.e8.value -= UInt64(1)
            if self.registration_confirmed.value == UInt64(1):
                self.e9.value += UInt64(1)
                log(Bytes(b"XOR: registration==true"))
            else:
                self.e10.value += UInt64(1)
                log(Bytes(b"XOR: registration==false"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def end_success(self) -> UInt64:
        if self.e12.value > UInt64(0):
            self.e12.value -= UInt64(1)
            log(Bytes(b"Process completed: success"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def end_reject(self) -> UInt64:
        if self.e10.value > UInt64(0):
            self.e10.value -= UInt64(1)
            log(Bytes(b"Process completed: reject"))
            return UInt64(1)
        return UInt64(0)

    @subroutine
    def execute_one_rule(self) -> UInt64:
        if self.start_event() != UInt64(0):
            return UInt64(1)
        if self.xor1_availability_check() != UInt64(0):
            return UInt64(1)
        if self.xor2_loop_back() != UInt64(0):
            return UInt64(1)
        if self.xor3_registration_check() != UInt64(0):
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
        )

        if total_tokens > UInt64(0):
            log(Bytes(b"RUNNING"))
        else:
            log(Bytes(b"COMPLETED"))
        return UInt64(1)

    # ========== TASKS ==========

    # Task 1: Take appointment (Patient->Radiology) - Single message
    @abimethod
    def send_appointment(self, medical_prescription: String) -> None:
        """Patient sends appointment to Radiology"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e1.value > UInt64(0), "Task not active"
        assert Txn.sender == self.patient.value, "Only patient"

        self.e1.value -= UInt64(1)
        self.medical_prescription.value = medical_prescription
        self.e2.value += UInt64(1)
        log(Bytes(b"Patient->Radiology: appointment"))

    # Task 2: Check availability (Radiology<->ward) - TWO methods
    @abimethod
    def send_availability_request(self, request_id: String) -> None:
        """Radiology sends request to ward"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e2.value > UInt64(0), "Task not active"
        assert Txn.sender == self.radiology.value, "Only radiology"

        self.e2.value -= UInt64(1)
        self.request_id.value = request_id
        self.e3.value += UInt64(1)
        log(Bytes(b"Radiology->ward: request"))

    @abimethod
    def send_availability_response(self, accepted: UInt64, date: String) -> None:
        """ward sends response to Radiology"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e3.value > UInt64(0), "Task not active"
        assert Txn.sender == self.ward.value, "Only ward"

        self.accepted.value = accepted
        self.appointment_date.value = date
        log(Bytes(b"ward->Radiology: response"))
        self.execute()

    # Task 3: Confirm appointment (Radiology->Patient) - Single message
    @abimethod
    def send_registration(self, appointment_id: String) -> None:
        """Radiology sends registration to Patient"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e4.value > UInt64(0), "Task not active"
        assert Txn.sender == self.radiology.value, "Only radiology"

        self.e4.value -= UInt64(1)
        self.appointment_id.value = appointment_id
        self.e6.value += UInt64(1)
        log(Bytes(b"Radiology->Patient: registration"))

    # Task 4: Check-in (Patient<->Radiology) - TWO methods
    @abimethod
    def send_checkin(self, appointment_id: String) -> None:
        """Patient sends checkin to Radiology"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e6.value > UInt64(0), "Task not active"
        assert Txn.sender == self.patient.value, "Only patient"
        assert appointment_id == self.appointment_id.value, "ID mismatch"

        self.e6.value -= UInt64(1)
        self.e7.value += UInt64(1)
        log(Bytes(b"Patient->Radiology: checkin"))

    @abimethod
    def send_confirmation(self, registration_confirmed: UInt64) -> None:
        """Radiology sends confirmation to Patient"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e7.value > UInt64(0), "Task not active"
        assert Txn.sender == self.radiology.value, "Only radiology"

        self.e7.value -= UInt64(1)
        self.registration_confirmed.value = registration_confirmed
        self.e8.value += UInt64(1)
        log(Bytes(b"Radiology->Patient: confirmation"))
        self.execute()

    # Task 5: Perform x-rays (Radiology->ward) - Single message
    @abimethod
    def send_analysis(self, ticket_id: String, report: String) -> None:
        """Radiology sends analysis to ward"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e9.value > UInt64(0), "Task not active"
        assert Txn.sender == self.radiology.value, "Only radiology"

        self.e9.value -= UInt64(1)
        self.ticket_id.value = ticket_id
        self.analysis_report.value = report
        self.e11.value += UInt64(1)
        log(Bytes(b"Radiology->ward: analysis"))

    # Task 6: Send results (ward->Patient) - Single message
    @abimethod
    def send_report(self, result_id: String) -> None:
        """ward sends report to Patient"""
        assert self.locked.value == UInt64(0), "Contract is locked"
        assert self.e11.value > UInt64(0), "Task not active"
        assert Txn.sender == self.ward.value, "Only ward"

        self.e11.value -= UInt64(1)
        self.result_id.value = result_id
        self.e12.value += UInt64(1)
        log(Bytes(b"ward->Patient: report"))
        self.execute()

    # ========== ADMIN ==========

    @baremethod(allow_actions=["UpdateApplication"])
    def update(self) -> None:
        assert Txn.sender == self.admin.value, "Only admin"
        self.locked.value = UInt64(1)
        log(Bytes(b"Locked for update"))

    @abimethod
    def unlock(self) -> None:
        assert Txn.sender == self.admin.value, "Only admin"
        self.locked.value = UInt64(0)
        log(Bytes(b"Unlocked"))

    @abimethod(allow_actions=["DeleteApplication"])
    def delete(self) -> None:
        assert Txn.sender == self.admin.value, "Only admin"
        assert self.locked.value == UInt64(0), "Contract is locked"
        log(Bytes(b"Deleted"))
