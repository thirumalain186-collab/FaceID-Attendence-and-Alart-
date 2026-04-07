from attendance_engine import AttendanceEngine

engine = AttendanceEngine()

print('Engine label_names (label_id -> person):')
for label_id, info in sorted(engine.label_names.items()):
    print(f'  Label {label_id}: {info["original_name"]}')

print()
print('Model expects:')
print('  Label 0 = manojkumar_1_student -> Manojkumar')
print('  Label 1 = manoj_2_student -> Manoj')
print('  Label 2 = thiru_3_student -> Thiru')
