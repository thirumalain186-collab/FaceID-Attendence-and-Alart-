"""
Remove/Delete a registered person
"""

import os
import shutil
import sqlite3
import config
from logger import get_logger

logger = get_logger()


def delete_person():
    """Delete a registered person"""
    
    print("\n" + "=" * 50)
    print("   DELETE REGISTERED PERSON")
    print("=" * 50)
    
    # Show all registered people
    try:
        conn = sqlite3.connect(str(config.DB_PATH))
        c = conn.cursor()
        c.execute("SELECT id, name, role, roll_number FROM people ORDER BY name")
        people = c.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Cannot read database: {e}")
        return
    
    if not people:
        logger.info("No registered people found")
        return
    
    print("\nRegistered People:")
    print("-" * 50)
    for i, p in enumerate(people, 1):
        print(f"{i}. {p[1]} ({p[2]}) - Roll: {p[3]}")
    print("-" * 50)
    
    # Get choice
    try:
        choice = int(input("\nEnter number to delete (0 to cancel): "))
        if choice == 0:
            logger.info("Cancelled by user")
            return
        if choice < 1 or choice > len(people):
            logger.error("Invalid choice")
            return
        
        person = people[choice - 1]
        person_id, name, role, roll = person
        
    except ValueError:
        logger.error("Please enter a number")
        return
    
    confirm = input(f"\nDelete '{name}' ({roll})? (yes/no): ").strip().lower()
    if confirm != 'yes':
        logger.info("Cancelled by user")
        return
    
    # Delete from database
    try:
        conn = sqlite3.connect(str(config.DB_PATH))
        c = conn.cursor()
        c.execute("DELETE FROM people WHERE id=?", (person_id,))
        c.execute("DELETE FROM attendance WHERE name=?", (name,))
        conn.commit()
        conn.close()
        logger.info("Deleted from database")
    except Exception as e:
        logger.exception(f"Database error: {e}")
        return
    
    safe_name = name.replace(" ", "_")
    for folder in config.DATASET_DIR.iterdir():
        if folder.is_dir() and folder.name.startswith(safe_name):
            shutil.rmtree(folder, ignore_errors=True)
            logger.info(f"Deleted images: {folder.name}")
    
    known_dir = config.KNOWN_FACES_DIR / name
    if known_dir.exists():
        shutil.rmtree(known_dir, ignore_errors=True)
        logger.info("Deleted reference images")
    
    if config.TRAINER_FILE.exists():
        os.remove(config.TRAINER_FILE)
        logger.warning("Model deleted - need to retrain")
    
    logger.info(f"Deleted: {name}")

if __name__ == "__main__":
    delete_person()
