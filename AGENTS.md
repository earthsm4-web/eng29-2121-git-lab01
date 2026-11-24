# AGENTS.md — กติกาสำหรับ AI และ Engineering Provenance (โปรเจกต์ transistor-simulator / Lab 4)

## ข้อห้ามเด็ดขาด (Do Not)

1. **ห้ามใช้ mock data หรือข้อมูลปลอมทดแทนผลจาก ngspice** ทุกกรณี ค่าตัวเลขในกราฟและตารางต้องมาจากผลการรัน ngspice จริงเท่านั้น
2. **ห้ามลบหรือแก้ไขโค้ดเดิมใน `bjt/bias.py`** (Analytical DC Bias สำหรับ Fixed, Emitter, Divider) รวมถึง `tests/*` ทั้งหมด
3. **ห้ามนำผลจาก `dc_bias.py` มาเปรียบเทียบในโหมด AC หรือ Transient** เปรียบเทียบได้เฉพาะโหมด DC ที่มีสมมติฐานสอดคล้องกันเท่านั้น (วงจร CE Voltage Divider เดียวกัน ค่าพารามิเตอร์เดียวกัน)
4. **ห้ามฮาร์ดโค้ดค่ากราฟ** หรือคำนวณสูตรสมการแบบประมาณแทนการจำลองจริง

## ข้อกำหนดการทำงาน (Requirements)

### spice_engine.py (Verified ngspice Adapter)
- ตรวจสอบการมีอยู่ของ binary `ngspice` ในระบบก่อนเรียกใช้ (เช่น `shutil.which`)
- สร้าง SPICE netlist จากพารามิเตอร์ที่ผ่านการ validate แล้ว
- เรียก ngspice ผ่าน `subprocess` รองรับ `.op`, `.ac`, `.tran`
- ดักจับ return code / stderr, กำหนด timeout ป้องกันโปรแกรมค้าง
- ตรวจสอบว่าไฟล์ผลลัพธ์ของ `.op` / `.ac` / `.tran` ถูกสร้างจริงและไม่ว่างเปล่าก่อนทำการ parse เสมอ
- แปลง/parse ผลลัพธ์เป็นโครงสร้างข้อมูลที่อ่านง่ายและระบุหน่วยชัดเจน

### app.py (Flask Dispatcher)
- Validate request parameters ก่อนส่งไปยัง `dc_bias.py` (Analytical) หรือ `spice_engine.py` (SPICE)
- Dispatch ตาม Analysis Mode: DC -> .op, AC -> .ac, Transient -> .tran
- แยกผลลัพธ์ของ SPICE กับ Analytical ออกจากกันชัดเจน ไม่ปนกัน
- เพิ่มส่วน Compare + Warnings ที่นำผลจาก `dc_bias.py` มาเทียบเฉพาะกรณีวิเคราะห์ DC ที่มีสมมติฐานสอดคล้องกัน

### UI / Presentation
- แยกป้ายบอกที่มา (Provenance) ชัดเจนระหว่าง "DC Analytical Results (dc_bias.py)" กับ "SPICE Simulation Results (ngspice)" ห้ามรวมเป็นค่าประเภทเดียวกัน
- แสดงหลักฐานการรันครบถ้วน: Netlist ที่ใช้รัน, Engine status, Plot values, Units, Saved run หรือข้อความ Error เมื่อรันไม่สำเร็จ
- แสดงค่าพร้อมหน่วยชัดเจน (V, mA, µA, kΩ, Hz, dB, องศา ฯลฯ)

## ค่าเริ่มต้นวงจรอ้างอิง CE Voltage Divider v1
| พารามิเตอร์ | ค่าเริ่มต้น |
|-------------|-------------|
| VCC | 12 V |
| RC | 2.2 kΩ |
| R1 | 100 kΩ |
| R2 | 22 kΩ |
| RE | 1 kΩ |
| RL | 10 kΩ |
| Source | 10 mV · 1 kHz |
| VBE | 0.70 V |
| Beta | 100 |

## โครงสร้างไฟล์ที่เกี่ยวข้องกับ Lab 4
```
app.py              Flask routes + dispatch (แก้ไขเพิ่มเติม)
bjt/bias.py         Analytical DC Bias (ห้ามแตะต้อง)
bjt/params.py       BiasParams (reuse)
bjt/validate.py     parse_form (reuse)
bjt/spice_engine.py | ngspice adapter (สร้างใหม่)
bjt/spice_plot.py   matplotlib graphs (สร้างใหม่)
templates/index.html| UI 3-cột + แท็บ DC/AC/Transient (แก้ไขเพิ่มเติม)
static/style.css    CSS เพิ่มเติมสำหรับ SPICE (แก้ไขเพิ่มเติม)
static/app.js       JavaScript โต้ตอบ UI (สร้างใหม่ ถ้าจำเป็น)
tests/              pytest suite (ห้ามลบ)
AGENTS.md           กติกานี้ (สร้างใหม่)
docs/validation.md  บันทึกผลทดสอบ vs ngspice จริง (อัปเดต)
docs/captures/      ภาพหน้าจอจากการทดสอบเบราว์เซอร์ (สร้างใหม่)
```
