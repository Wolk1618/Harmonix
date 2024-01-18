# Harmonix
Here is a lab group project from Imperial College London Applied Machine Learning MsC

More to come

How to modify the address of the ToF:

Use this link: 

https://www.st.com/resource/en/user_manual/um2884-a-guide-to-using-the-vl53l5cx-multizone-timeofflight-ranging-sensor-with-wide-field-of-view-ultra-lite-driver-uld-stmicroelectronics.pdf

Follow steps (i.e. pull up, pull down, etc.).

// Initialize the second sensor (Dev2) with a new address
Dev2.platform.address = VL53L5CX_DEFAULT_I2C_ADDRESS; // Temporarily use default address for initialization
Dev2.platform.port = i2c_port;

uint16_t new_address2 = 0x20; // New I2C address for Dev2
//vl53l5cx_set_i2c_address(&Dev2, new_address2);
//Dev2.platform.address = new_address2; // Update the address in the device configuration

Run the following code, then un-comment the bottom two linesm and comment the set_i2c_adresss and the Dev2.platform.adresss... etc. then run it again, et voila!



