#!/usr/bin/env python3
"""
rear_side_combined.py

Flow:
1) On start: rotate rear servo to 90° (active) and start rear DC motor.
2) Then start side-arm detection subprocess (detect.py ... --nosave).
3) Side-arm logic runs: when paddy NOT detected -> side servo -> side DC motor ON;
   when paddy detected -> stop side DC motor and servo to default (0°).

Wiring assumptions (must match your hardware):
- Side (existing):
    SIDE_SERVO_PIN = 18    # Physical Pin 12 (side servo signal)
    SIDE_DC_ENABLE = 12    # Physical Pin 32 (L293D EN for side)
    SIDE_DC_INPUT1 = 23    # Physical Pin 16 (L293D IN1 for side)
    SIDE_DC_INPUT2 = 24    # Physical Pin 18 (L293D IN2 for side)
- Rear (new on same L293D second H-bridge):
    REAR_SERVO_PIN = 17    # Physical Pin 11 (rear servo signal)
    REAR_DC_ENABLE = 25    # Physical Pin 22 (L293D EN for rear)
    REAR_DC_INPUT1 = 27    # Physical Pin 13 (L293D IN1 for rear)
    REAR_DC_INPUT2 = 22    # Physical Pin 15 (L293D IN2 for rear)

Make sure:
- L293D pin16 (Vcc1 logic) -> Pi 5V (Pin 2 or 4)
- L293D pin8 (Vcc2 motor) -> External motor + (5V motor rail)
- All grounds common (Pi GND Pin 6, L293D GND pins, motor supply -)
- Servos powered from external 5-6V supply; signal lines to Pi GPIOs above.
"""

import os
import sys
import subprocess
import threading
import time
import re
import traceback
from typing import Optional

import RPi.GPIO as GPIO

# ====== YOLO / detect.py settings (adjust paths if needed) ======
YOLOV5_DIR = "/home/miniproj/minip/yolov5"
MODEL_PATH = "paddy_model.pt"
PYTHON_CMD = sys.executable
DETECT_CMD = [
    PYTHON_CMD, "detect.py",
    "--weights", MODEL_PATH,
    "--source", "0",
    "--device", "cpu",
    "--nosave"
]

# ====== SIDE ARM GPIO (existing) ======
SIDE_SERVO_PIN = 18        # Physical Pin 12 (side servo signal)
SIDE_DC_ENABLE = 12        # L293D Enable pin (Physical Pin 32)
SIDE_DC_INPUT1 = 23        # L293D Input 1 (Physical Pin 16)
SIDE_DC_INPUT2 = 24        # L293D Input 2 (Physical Pin 18)

# ====== REAR ARM GPIO (new) ======
REAR_SERVO_PIN = 17        # Physical Pin 11 (rear servo signal)
REAR_DC_ENABLE = 25        # L293D Enable pin for rear DC (Physical Pin 22)
REAR_DC_INPUT1 = 27        # L293D Input 1 for rear (Physical Pin 13)
REAR_DC_INPUT2 = 22        # L293D Input 2 for rear (Physical Pin 15)

# ====== SERVO ANGLES ======
SERVO_DEFAULT = 0     # Default position (arm UP)
SERVO_ACTIVE = 90     # Active position (arm DOWN)

# ====== DETECTION / MOTOR SETTINGS ======
KEYWORD = "paddy"
BUFFER_SIZE = 5
MAJORITY_REQUIRED = 3
SIDE_DC_SPEED = 80   # percent PWM for side DC when tilling
REAR_DC_SPEED = 80   # percent PWM for rear DC when active

# ====== GPIO SETUP ======
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup side pins
GPIO.setup(SIDE_SERVO_PIN, GPIO.OUT)
GPIO.setup(SIDE_DC_ENABLE, GPIO.OUT)
GPIO.setup(SIDE_DC_INPUT1, GPIO.OUT)
GPIO.setup(SIDE_DC_INPUT2, GPIO.OUT)

# Setup rear pins
GPIO.setup(REAR_SERVO_PIN, GPIO.OUT)
GPIO.setup(REAR_DC_ENABLE, GPIO.OUT)
GPIO.setup(REAR_DC_INPUT1, GPIO.OUT)
GPIO.setup(REAR_DC_INPUT2, GPIO.OUT)

# PWM objects
pwm_servo_side = GPIO.PWM(SIDE_SERVO_PIN, 50)      # 50Hz for servo
pwm_servo_side.start(0)

pwm_servo_rear = GPIO.PWM(REAR_SERVO_PIN, 50)
pwm_servo_rear.start(0)

pwm_dc_side = GPIO.PWM(SIDE_DC_ENABLE, 1000)      # 1kHz for DC motor enable
pwm_dc_side.start(0)

pwm_dc_rear = GPIO.PWM(REAR_DC_ENABLE, 1000)
pwm_dc_rear.start(0)


# ====== HELPER: SERVO CONTROL (generic) ======
def set_servo_angle(pwm_obj, pin, angle, hold_time=0.6):
    """
    Set servo to specific angle immediately.
    pwm_obj: PWM object for that servo
    pin: signal pin (for toggling output on/off)
    angle: 0-180
    """
    # Standard mapping: duty = 2 + angle/18
    duty = 2 + (angle / 18.0)
    GPIO.output(pin, True)
    pwm_obj.ChangeDutyCycle(duty)
    time.sleep(hold_time)
    GPIO.output(pin, False)
    pwm_obj.ChangeDutyCycle(0)


# ====== REAR ARM CONTROL ======
def rear_activate():
    """Rotate rear servo to active position and start rear DC motor."""
    print("=== ACTIVATING REAR ARM ===")
    set_servo_angle(pwm_servo_rear, REAR_SERVO_PIN, SERVO_ACTIVE)
    time.sleep(0.25)
    GPIO.output(REAR_DC_INPUT1, GPIO.HIGH)
    GPIO.output(REAR_DC_INPUT2, GPIO.LOW)
    pwm_dc_rear.ChangeDutyCycle(REAR_DC_SPEED)
    print("Rear DC motor started.")


def rear_deactivate():
    """Stop rear DC motor and return servo to default."""
    print("=== DEACTIVATING REAR ARM ===")
    pwm_dc_rear.ChangeDutyCycle(0)
    GPIO.output(REAR_DC_INPUT1, GPIO.LOW)
    GPIO.output(REAR_DC_INPUT2, GPIO.LOW)
    time.sleep(0.25)
    set_servo_angle(pwm_servo_rear, REAR_SERVO_PIN, SERVO_DEFAULT)
    print("Rear arm returned to default.")


# ====== SIDE ARM CONTROL (functions) ======
def side_dc_start(speed=SIDE_DC_SPEED):
    GPIO.output(SIDE_DC_INPUT1, GPIO.HIGH)
    GPIO.output(SIDE_DC_INPUT2, GPIO.LOW)
    pwm_dc_side.ChangeDutyCycle(speed)
    print(f"Side DC motor start @ {speed}%")


def side_dc_stop():
    pwm_dc_side.ChangeDutyCycle(0)
    GPIO.output(SIDE_DC_INPUT1, GPIO.LOW)
    GPIO.output(SIDE_DC_INPUT2, GPIO.LOW)
    print("Side DC motor stop")


def side_servo_set(angle):
    set_servo_angle(pwm_servo_side, SIDE_SERVO_PIN, angle)


def side_activate_tilling():
    print("Side: NO PADDY DETECTED - Activating side tilling")
    side_servo_set(SERVO_ACTIVE)
    time.sleep(0.2)
    side_dc_start()
    print("Side tilling active.")


def side_deactivate_tilling():
    print("Side: PADDY DETECTED - Deactivating side tilling")
    side_dc_stop()
    time.sleep(0.2)
    side_servo_set(SERVO_DEFAULT)
    print("Side tilling deactivated.")


# ====== DETECT SUBPROCESS CLASS ======
class DetectSubprocess:
    def __init__(self, cwd, cmd):
        self.cwd = cwd
        self.cmd = cmd
        self.proc: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()

    def start(self):
        print("Launching detect.py subprocess:")
        print("  cwd:", self.cwd)
        print("  cmd:", " ".join(self.cmd))
        self.proc = subprocess.Popen(
            self.cmd,
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

    def stop(self):
        self._stop_event.set()
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
            except Exception:
                pass

    def stdout_lines(self):
        if self.proc is None:
            return
        try:
            for line in self.proc.stdout:
                if self._stop_event.is_set():
                    break
                yield line.rstrip("\n")
        except Exception:
            return


# ====== Side detector runner (separate thread) ======
def run_side_detector():
    detector = DetectSubprocess(cwd=YOLOV5_DIR, cmd=DETECT_CMD)
    detector.start()

    detection_buffer = []
    arm_active = False
    frame_counter = 0

    try:
        for line in detector.stdout_lines():
            frame_counter += 1
            text = line.strip()
            if not text:
                continue

            print(f"[detect.py] {text}")

            lower = text.lower()
            paddy_detected = False

            if "no detections" in lower:
                paddy_detected = False
            elif KEYWORD in lower:
                paddy_detected = True
            else:
                m = re.search(r'\b(\d+)\s+([a-z_]+)\b', lower)
                if m and KEYWORD in m.group(2):
                    paddy_detected = True

            detection_buffer.append(bool(paddy_detected))
            if len(detection_buffer) > BUFFER_SIZE:
                detection_buffer.pop(0)

            stable_paddy_detection = sum(detection_buffer) >= MAJORITY_REQUIRED

            # Side arm logic
            if not stable_paddy_detection and not arm_active:
                side_activate_tilling()
                arm_active = True
            elif stable_paddy_detection and arm_active:
                side_deactivate_tilling()
                arm_active = False

            status = f"Paddy: {'YES' if stable_paddy_detection else 'NO '} | SideArm: {'ACTIVE' if arm_active else 'DEFAULT'}"
            print(f"\r{status}", end='', flush=True)

            time.sleep(0.05)

    except Exception as e:
        print("Side detector thread error:", e)
        traceback.print_exc()
    finally:
        print("\nSide detector stopping...")
        detector.stop()
        side_dc_stop()
        side_servo_set(SERVO_DEFAULT)


# ====== MAIN FLOW ======
def main():
    try:
        print("System starting...")
        # Initialize both arms to default (side default; rear will activate)
        side_servo_set(SERVO_DEFAULT)
        side_dc_stop()

        # Ensure rear motor off and rear servo at default before activation
        set_servo_angle(pwm_servo_rear, REAR_SERVO_PIN, SERVO_DEFAULT, hold_time=0.3)
        pwm_dc_rear.ChangeDutyCycle(0)
        GPIO.output(REAR_DC_INPUT1, GPIO.LOW)
        GPIO.output(REAR_DC_INPUT2, GPIO.LOW)

        time.sleep(0.5)

        # 1) Rear arm: rotate and start motor
        rear_activate()

        # 2) Now start the side-arm detector in a background thread
        side_thread = threading.Thread(target=run_side_detector, daemon=True)
        side_thread.start()

        print("Side detector started. Press Ctrl+C to stop.")
        # Keep main thread alive while side detector runs
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Shutting down...")

    except Exception as e:
        print("Fatal error:", e)
        traceback.print_exc()

    finally:
        # Cleanup sequence
        print("Stopping rear and side motors, returning servos to default...")
        try:
            # Stop rear motor and return rear servo
            rear_deactivate()

            # Ensure side arm stopped and returned
            side_dc_stop()
            side_servo_set(SERVO_DEFAULT)

            time.sleep(0.5)

            # Stop PWMs
            pwm_servo_side.stop()
            pwm_servo_rear.stop()
            pwm_dc_side.stop()
            pwm_dc_rear.stop()

            GPIO.cleanup()
        except Exception:
            traceback.print_exc()

        print("Shutdown complete.")


if __name__ == "__main__":
    main()
