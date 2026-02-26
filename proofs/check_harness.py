"""
check_harness.py
Shared test harness for proof scripts.

No dependencies beyond stdlib.
"""

import sys


class CheckHarness:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = []

    def check(self, label, actual, expected, tol=1e-4):
        if abs(actual - expected) <= tol:
            print(f"  PASS  {label}: {actual:.6f}")
            self.passed += 1
        else:
            print(f"  FAIL  {label}: got {actual:.6f}, expected {expected:.6f}  (delta={abs(actual-expected):.6f})")
            self.failed += 1

    def check_true(self, label, condition, detail=""):
        if condition:
            print(f"  PASS  {label}")
            self.passed += 1
        else:
            print(f"  FAIL  {label}  {detail}")
            self.failed += 1

    def warn(self, msg):
        self.warnings.append(msg)
        print(f"  WARN  {msg}")

    def summary(self, domain_label=""):
        print(f"\n{'='*60}")
        if domain_label:
            print(f"Results ({domain_label}): {self.passed} passed, {self.failed} failed"
                  + (f", {len(self.warnings)} warnings" if self.warnings else ""))
        else:
            print(f"Results: {self.passed} passed, {self.failed} failed"
                  + (f", {len(self.warnings)} warnings" if self.warnings else ""))
        if self.warnings:
            print("\nWarnings:")
            for w in self.warnings:
                print(f"  {w}")

    def exit(self):
        sys.exit(0 if self.failed == 0 else 1)
