"""
JSON Schema validation utilities for output files.

Validates JSONL files against their defined schemas to ensure
format compliance.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

try:
    import jsonschema
    from jsonschema import validate
    from jsonschema.exceptions import (
        ValidationError as JsonschemaValidationError
    )
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    JsonschemaValidationError = Exception

from src.utils.jsonl_utils import JSONLHandler

_logger = logging.getLogger(__name__)


class SchemaValidator:
    """
    Validates JSONL files against JSON schemas.
    
    Encapsulation:
    - All internal state uses name-mangled attributes
    - Public API via class methods
    """
    
    def __init__(self) -> None:
        """Initialize validator with private state."""
        self.__validated_count: int = 0
        self.__error_count: int = 0
        self.__errors: List[str] = []
    
    @property
    def validated_count(self) -> int:
        """Get number of records validated (read-only)."""
        return self.__validated_count
    
    @property
    def error_count(self) -> int:
        """Get number of validation errors (read-only)."""
        return self.__error_count
    
    @property
    def errors(self) -> List[str]:
        """Get validation errors (read-only copy)."""
        return self.__errors.copy()
    
    @classmethod
    def load_schema(cls, schema_path: Path) -> Dict[str, Any]:
        """
        Load JSON schema from file.
        
        Parameters
        ----------
        schema_path : Path
            Path to schema JSON file
        
        Returns
        -------
        Dict[str, Any]
            Loaded schema dictionary
        
        Raises
        ------
        FileNotFoundError
            If schema file doesn't exist
        json.JSONDecodeError
            If schema file is invalid JSON
        """
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with schema_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    
    def validate_file(
        self,
        jsonl_path: Path,
        schema_path: Path,
        strict: bool = False,
    ) -> bool:
        """
        Validate a JSONL file against a schema.
        
        Parameters
        ----------
        jsonl_path : Path
            Path to JSONL file to validate
        schema_path : Path
            Path to JSON schema file
        strict : bool
            If True, stop on first error. If False, collect all errors.
        
        Returns
        -------
        bool
            True if all records are valid, False otherwise
        """
        if not JSONSCHEMA_AVAILABLE:
            _logger.warning(
                "jsonschema library not available. Skipping validation."
            )
            return True
        
        try:
            schema = self.load_schema(schema_path)
            records = JSONLHandler.load(jsonl_path)
            return self._validate_records(records, schema, strict)
        except Exception as e:
            _logger.error("Schema validation failed: %s", e)
            return False
    
    def _validate_records(
        self,
        records: List[Dict[str, Any]],
        schema: Dict[str, Any],
        strict: bool,
    ) -> bool:
        """Validate all records against schema."""
        self.__validated_count = 0
        self.__error_count = 0
        self.__errors = []
        
        for idx, record in enumerate(records, start=1):
            if not self._validate_single_record(record, schema, idx, strict):
                if strict:
                    return False
        
        return self._log_validation_results(len(records))
    
    def _validate_single_record(
        self,
        record: Dict[str, Any],
        schema: Dict[str, Any],
        idx: int,
        strict: bool,
    ) -> bool:
        """Validate a single record against schema."""
        try:
            validate(instance=record, schema=schema)
            self.__validated_count += 1
            return True
        except JsonschemaValidationError as e:
            self._record_validation_error(record, idx, e)
            return False
    
    def _record_validation_error(
        self,
        record: Dict[str, Any],
        idx: int,
        error: JsonschemaValidationError,
    ) -> None:
        """Record a validation error."""
        self.__error_count += 1
        section_id = record.get('section_id', 'unknown')
        error_msg = (
            f"Record {idx} (section_id={section_id}): {error.message}"
        )
        self.__errors.append(error_msg)
        _logger.warning(error_msg)
    
    def _log_validation_results(self, total_records: int) -> bool:
        """Log validation results and return success status."""
        if self.__error_count > 0:
            _logger.warning(
                "Validation completed with %d errors out of %d records",
                self.__error_count,
                total_records
            )
            return False
        
        _logger.info(
            "Validation successful: %d records validated",
            self.__validated_count
        )
        return True
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"SchemaValidator("
            f"validated={self.__validated_count}, "
            f"errors={self.__error_count})"
        )
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return "SchemaValidator()"
    
    def __len__(self) -> int:
        """Return number of validated records."""
        return self.__validated_count
    
    def __bool__(self) -> bool:
        """Truthiness: True if validation passed."""
        return self.__error_count == 0
