"""
Basic tests for scrapers and validators
"""

import pytest
from utils.validators import URLValidator, SalaryValidator, ExperienceValidator


class TestURLValidator:
    """Test URL validation"""
    
    def test_valid_url(self):
        assert URLValidator.is_valid_url("https://example.com")
        assert URLValidator.is_valid_url("http://djinni.co/jobs/123")
    
    def test_invalid_url(self):
        assert not URLValidator.is_valid_url("not a url")
        assert not URLValidator.is_valid_url("ftp://example.com")
    
    def test_djinni_detection(self):
        assert URLValidator.is_djinni_url("https://djinni.co/jobs/123")
        assert not URLValidator.is_djinni_url("https://dou.ua/jobs")
    
    def test_dou_detection(self):
        assert URLValidator.is_dou_url("https://dou.ua/jobs/123")
        assert not URLValidator.is_dou_url("https://djinni.co")
    
    def test_source_detection(self):
        assert URLValidator.get_source_from_url("https://djinni.co/jobs/1") == "djinni"
        assert URLValidator.get_source_from_url("https://dou.ua/jobs/1") == "dou"
        assert URLValidator.get_source_from_url("https://other.com") is None


class TestSalaryValidator:
    """Test salary parsing"""
    
    def test_parse_range(self):
        min_sal, max_sal = SalaryValidator.parse_salary_range("$1000 - $2000")
        assert min_sal == 1000
        assert max_sal == 2000
    
    def test_parse_single_value(self):
        min_sal, max_sal = SalaryValidator.parse_salary_range("$2000")
        assert min_sal == 2000
        assert max_sal == 2000
    
    def test_parse_without_currency(self):
        min_sal, max_sal = SalaryValidator.parse_salary_range("1000 - 2000")
        assert min_sal == 1000
        assert max_sal == 2000
    
    def test_valid_range(self):
        assert SalaryValidator.is_valid_salary_range(1000, 2000)
        assert SalaryValidator.is_valid_salary_range(2000, 2000)
        assert not SalaryValidator.is_valid_salary_range(2000, 1000)


class TestExperienceValidator:
    """Test experience parsing"""
    
    def test_parse_years(self):
        assert ExperienceValidator.parse_experience_years("2+ years") == 2
        assert ExperienceValidator.parse_experience_years("3-5 years") == 3
        assert ExperienceValidator.parse_experience_years("1 year experience") == 1
    
    def test_level_from_experience(self):
        assert ExperienceValidator.get_level_from_experience(1) == "junior"
        assert ExperienceValidator.get_level_from_experience(3) == "middle"
        assert ExperienceValidator.get_level_from_experience(6) == "senior"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
