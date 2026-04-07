"""
Configure Email Alerts for Monitoring Mode
Sets up SMTP credentials and recipient emails
"""

import os
import sys
from pathlib import Path

def setup_email_config():
    """Interactive email configuration setup"""
    
    print("\n" + "="*70)
    print("EMAIL ALERTS CONFIGURATION SETUP")
    print("="*70)
    print("\nThis will configure email alerts for the monitoring mode.")
    print("Alerts are sent when unknown/unauthorized persons are detected.\n")
    
    # Check if .env exists
    env_file = Path(".env")
    existing_config = {}
    
    if env_file.exists():
        print("[OK] Found existing .env file")
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    existing_config[key.strip()] = value.strip().strip('"\'')
        
        print("\nExisting configuration:")
        for key in ["EMAIL_ENABLED", "SENDER_EMAIL", "CLASS_ADVISOR_EMAIL", "HOD_EMAIL"]:
            value = existing_config.get(key, "[NOT SET]")
            if key == "SENDER_PASSWORD" and value != "[NOT SET]":
                print(f"  {key}: ****[hidden]****")
            else:
                print(f"  {key}: {value}")
    else:
        print("[NOTE] No .env file found - will create new one")
    
    print("\n" + "="*70)
    print("STEP 1: Gmail Sender Configuration")
    print("="*70)
    print("""
You need a Gmail account to send alerts.
For Gmail with 2-factor authentication:
  1. Go to myaccount.google.com/apppasswords
  2. Select "Mail" and "Windows Computer"
  3. Google will show a 16-character app password
  4. Use that password below (NOT your Gmail password)

For regular Gmail without 2FA:
  - You can use your regular Gmail password
  - But 2FA with app password is MORE SECURE (recommended)
    """)
    
    sender_email = input("Gmail address (sender): ").strip()
    if not sender_email or "@gmail.com" not in sender_email:
        print("[ERROR] Please enter a valid Gmail address")
        return False
    
    sender_password = input("Gmail app password (or password): ").strip()
    if len(sender_password) < 8:
        print("[ERROR] Password too short")
        return False
    
    print("\n" + "="*70)
    print("STEP 2: Recipient Configuration")
    print("="*70)
    
    advisor_email = input("Class Advisor email address: ").strip()
    if advisor_email and "@" not in advisor_email:
        print("[ERROR] Invalid email address for advisor")
        return False
    
    hod_email = input("HOD (Head of Department) email address: ").strip()
    if hod_email and "@" not in hod_email:
        print("[ERROR] Invalid email address for HOD")
        return False
    
    if not advisor_email and not hod_email:
        print("[ERROR] At least one recipient email is required")
        return False
    
    print("\n" + "="*70)
    print("STEP 3: Configuration Summary")
    print("="*70)
    
    print(f"\nSender: {sender_email}")
    print(f"Class Advisor: {advisor_email or '[NOT SET]'}")
    print(f"HOD: {hod_email or '[NOT SET]'}")
    
    # Test configuration
    print("\nTesting email configuration...")
    test_choice = input("Send test email before saving? (yes/no): ").strip().lower()
    
    if test_choice == "yes":
        print("Testing email connection...")
        try:
            import smtplib
            import ssl
            
            context = ssl.create_default_context()
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
            print("[OK] Email credentials are valid!")
        except Exception as e:
            print(f"[ERROR] Email test failed: {e}")
            print("Please check your credentials and try again")
            retry = input("Continue anyway? (yes/no): ").strip().lower()
            if retry != "yes":
                return False
    
    # Save configuration
    print("\n" + "="*70)
    print("SAVING CONFIGURATION")
    print("="*70)
    
    try:
        # Read existing .env content
        existing_content = ""
        if env_file.exists():
            with open(env_file, "r") as f:
                existing_content = f.read()
        
        # Update or add configuration
        config_dict = existing_config.copy()
        config_dict["EMAIL_ENABLED"] = "true"
        config_dict["SENDER_EMAIL"] = sender_email
        config_dict["SENDER_PASSWORD"] = sender_password
        config_dict["CLASS_ADVISOR_EMAIL"] = advisor_email
        config_dict["HOD_EMAIL"] = hod_email
        
        # Build new content
        new_lines = []
        processed_keys = set()
        
        # Update existing lines
        if existing_content:
            for line in existing_content.split("\n"):
                if "=" in line and not line.strip().startswith("#"):
                    key = line.split("=")[0].strip()
                    if key in config_dict:
                        new_lines.append(f'{key}="{config_dict[key]}"')
                        processed_keys.add(key)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
        
        # Add new keys
        for key, value in config_dict.items():
            if key not in processed_keys:
                new_lines.append(f'{key}="{value}"')
        
        # Write .env file
        with open(env_file, "w") as f:
            f.write("\n".join(new_lines))
        
        print(f"\n[OK] Configuration saved to {env_file}")
        
        print("\n" + "="*70)
        print("CONFIGURATION COMPLETE!")
        print("="*70)
        print(f"""
Email alerts are now configured!

Recipients:
  - Class Advisor: {advisor_email}
  - HOD: {hod_email}

To start monitoring with email alerts:
  python monitoring_with_alerts.py

How it works:
  1. Start monitoring mode
  2. Registered students are marked without alerts
  3. Unknown/unauthorized persons trigger instant email alerts
  4. Photos of unknown persons are saved and attached
  5. Both advisor and HOD receive emails

Next steps:
  1. Test the system: python monitoring_with_alerts.py
  2. Check logs in logs/ directory
  3. View captured unknown faces in captured_alerts/ directory
        """)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to save configuration: {e}")
        return False


def main():
    """Main entry point"""
    try:
        success = setup_email_config()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[OK] Setup cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
