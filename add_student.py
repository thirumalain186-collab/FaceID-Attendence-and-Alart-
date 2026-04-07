import database

# Add Raj to database
person_id = database.add_person(
    name='Raj',
    role='student',
    roll_number='02'
)

if person_id:
    print(f"Added Raj to database (ID: {person_id})")
    
    # Train
    print("\nTraining model...")
    import train
    success = train.train_model()
    
    if success:
        print("Training successful!")
        
        # Show all students
        print("\nAll registered students:")
        people = database.get_active_people()
        for p in people:
            print(f"  - {p.get('name')} (Roll: {p.get('roll_number')})")
    else:
        print("Training failed")
else:
    print("Failed to add to database")
