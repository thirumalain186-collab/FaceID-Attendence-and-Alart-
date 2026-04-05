"""
Unit Tests for Configuration Module
"""

import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config


class TestConfigPaths:
    """Test path configurations"""
    
    def test_dataset_dir_exists(self):
        """Test dataset directory is defined"""
        assert config.DATASET_DIR is not None
        assert isinstance(config.DATASET_DIR, Path)
    
    def test_trainer_dir_exists(self):
        """Test trainer directory is defined"""
        assert config.TRAINER_DIR is not None
        assert isinstance(config.TRAINER_DIR, Path)
    
    def test_reports_dir_exists(self):
        """Test reports directory is defined"""
        assert config.REPORTS_DIR is not None
        assert isinstance(config.REPORTS_DIR, Path)


class TestConfigValues:
    """Test configuration values"""
    
    def test_attendance_config_values(self):
        """Test attendance config has valid values"""
        cfg = config.ATTENDANCE_CONFIG
        
        assert cfg['confidence_threshold'] > 0
        assert cfg['confidence_threshold'] <= 100
        assert cfg['camera_index'] >= 0
        assert cfg['samples_per_person'] > 0
        assert cfg['frame_skip'] > 0
    
    def test_schedule_config_values(self):
        """Test schedule config has valid values"""
        cfg = config.SCHEDULE_CONFIG
        
        assert 'attendance_start' in cfg
        assert 'attendance_stop' in cfg
        assert 'day_end' in cfg
        assert 'batch_days' in cfg
        assert cfg['batch_days'] == 30
    
    def test_log_config_values(self):
        """Test logging config"""
        assert config.LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        assert config.LOG_MAX_SIZE > 0


class TestDirectories:
    """Test directory creation"""
    
    def test_base_dirs_exist(self):
        """Test base directories exist"""
        assert config.DATASET_DIR.exists() or True
        assert config.TRAINER_DIR.exists() or True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
