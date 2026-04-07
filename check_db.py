import database

people = database.get_active_people()
print(f"Registered people: {len(people)}")
for p in people:
    print(f"  Name: {p.get('name')}, Roll: {p.get('roll_number')}")
