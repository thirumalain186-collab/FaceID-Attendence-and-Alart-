import database

# Check what get_active_people returns
people = database.get_active_people()
print(f'Active people: {len(people)}')
for p in people:
    print(f'  ID: {p.get("id")}, Name: {p.get("name")}, Roll: {p.get("roll_number")}')
