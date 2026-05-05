# paddy-weed-removal-system

An autonomous precision agriculture system for real-time weed detection and mechanical removal using computer vision and embedded control.


---

## INTRODUCTION

### OVERVIEW

The rapid growth of the global population has necessitated a paradigm shift in agricultural practices, leading to the emergence of "smart farming" and "precision agriculture." At the forefront of this revolution are AI-driven robotics designed to optimize resource usage and maximize yield. Weed infestation remains one of the most persistent challenges in agriculture, traditionally managed through broad-spectrum herbicides or manual labour. Both methods are increasingly viewed as economically inefficient and environmentally unsustainable.

This project introduces the "Intelligent Agri-Tronic Weeder," a system that applies the principles of precision agriculture to solve the problem of weed management. By integrating a hardware-software system, this initiative represents a progression from static image-based analysis to dynamic, real-time video processing capable of operating in outdoor environments. The system is designed to distinguish between crops and weeds using deep learning and perform targeted mechanical removal, thereby eliminating the need for chemicals.

---

### PROBLEM STATEMENT

Current weed management solutions are inefficient and unsustainable. While deep learning models offer high accuracy in object detection, their deployment on resource-constrained edge platforms like the Raspberry Pi for real-time operation presents significant engineering challenges. These challenges include managing computational load, ensuring low latency for real-time actuation, and integrating diverse hardware components.

The primary problem this project addresses is the lack of an accessible, cost-effective, and autonomous system that can perform precision weeding without the use of chemicals. Existing solutions are often too expensive for small-scale farmers or lack the intelligence to operate autonomously in dynamic field conditions.

---

### OBJECTIVES

The primary objective of this project is to build a functional and efficient prototype of an autonomous weeding robot. The specific objectives are as follows:

- Develop a Vision System: To develop a robust CNN Model for real-time weed and crop detection.  
- Edge Implementation: To implement and optimize the AI model on a Raspberry Pi 4 Model B, ensuring acceptable inference speeds for real-time operation.  
- Mechanical Integration: To design and integrate a mechanical tilling end-effector actuated by servo and DC motors that can physically remove weeds based on visual feedback.  
- System Integration: To demonstrate a seamless, end-to-end workflow from image acquisition to physical actuation, creating a fully autonomous "detect-and-act" cycle.  
- Cost-Effectiveness: To utilize off-the-shelf components (Raspberry Pi, standard motors, chassis) to ensure the system remains affordable and replicable.  

---

## METHODOLOGY

The methodology for this project is divided into three primary components: the AI Vision System, the Control Logic, and the Hardware Actuation. The system is designed to operate in real-time, processing visual data to make immediate decisions about weed removal.

The system architecture is centralized around a Raspberry Pi 4 Model B, which serves as the primary processing unit and controller. The data flow within the system is linear and hierarchical, organized into three distinct layers: the Input Layer, the Processing Layer, and the Actuation Layer.

- Input Layer: USB camera module capturing real-time video frames  
- Processing Layer: YOLOv5n model running on Raspberry Pi  
- Actuation Layer: Motor driver and electromechanical actuators  

The control logic unit determines whether to trigger the weeding mechanism based on the presence or absence of a crop in the camera's field of view.

---

## SYSTEM REQUIREMENTS

### HARDWARE REQUIREMENTS

- Raspberry Pi 4 Model B  
- Zebronics USB Webcam  
- MG996R Servo Motors (x2)  
- DC Tilling Motors (x2)  
- L293D Motor Driver  
- 5V 3A Power Bank  
- Common Ground Wiring  

---

### SOFTWARE REQUIREMENTS

- Raspberry Pi OS Lite (64-bit)  
- Python 3.11  
- PyTorch (v2.0.1)  
- Torchvision (v0.15.2)  
- Ultralytics YOLOv5  
- OpenCV (opencv-python-headless)  
- RPi.GPIO  
- Google Colab  
- Roboflow  

---

## IMPLEMENTATION

### DATA ACQUISITION AND PREPARATION

- Dataset of Paddy crops sourced from Roboflow Universe  
- Images resized to 640x640  
- Exported in YOLOv5 PyTorch format  

### AI MODEL TRAINING

- Transfer Learning using yolov5n.pt  
- Training epochs: 100  
- Batch size: 16  
- Training environment: Google Colab (Tesla T4 GPU)  

Command used: python train.py --img 640 --batch 16 --epochs 100 --data data.yaml --weights yolov5n.pt


### CONTROL LOGIC

- SAFE Mode (Paddy Detected): Servo at 0°, motor OFF  
- WEEDING Mode (No Paddy): Servo at 90°, motor ON  

The system continuously processes frames and updates the physical state of the robot in real-time.

---

## RESULTS

### DETECTION ACCURACY

- Mean Average Precision: over 95%  
- Inference Speed: 3-5 FPS on Raspberry Pi  

### ACTUATION RESPONSE

- Latency: approximately 2 seconds  
- Accurate switching between Safe and Active modes  
- Efficient and targeted soil disturbance  

The system successfully demonstrated the "Detect-and-Act" logic.

---

## CONCLUSION

The "Intelligent Agri-Tronic Weeder" mini-project successfully demonstrated the feasibility of developing a low-cost, autonomous precision agriculture robot. By integrating state-of-the-art computer vision (YOLOv5) with a custom-built mechanical platform, we achieved the core objective of targeted, chemical-free weed management.

### SUMMARY OF ACHIEVEMENTS

- Cost-Effective Design  
- Autonomous Operation  
- Scalable Architecture  

This project serves as a solid foundation for future research into sustainable, AI-driven agricultural solutions.
