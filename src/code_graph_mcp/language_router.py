"""
Language detection and routing system for multi-language code analysis.

This module provides intelligent language detection, project structure analysis,
and routing to appropriate parsers and analyzers based on file content and patterns.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
import json
import logging
import mimetypes
import re

from .universal_parser import LanguageRegistry, LanguageConfig

logger = logging.getLogger(__name__)


@dataclass
class ProjectProfile:  # pylint: disable=too-many-instance-attributes
    """Profile of a project's language composition and structure."""

    primary_language: str  # Most prevalent language
    languages: Dict[str, int]  # Language -> file count
    total_files: int  # Total analyzable files
    confidence_score: float  # Detection confidence (0-1)

    # Project characteristics
    framework_hints: List[str]  # Detected frameworks/libraries
    build_system: Optional[str]  # Build system (npm, cargo, maven, etc.)
    project_type: str  # web, mobile, desktop, library, etc.

    # File organization
    source_directories: List[Path]  # Main source code directories
    test_directories: List[Path]  # Test code directories
    config_files: List[Path]  # Configuration files

    # Quality indicators
    has_tests: bool  # Project has test files
    has_documentation: bool  # Project has documentation
    has_ci_config: bool  # Project has CI/CD configuration


class LanguageDetector:  # pylint: disable=too-few-public-methods
    """Intelligent language detection using multiple heuristics."""

    def __init__(self):
        self.registry = LanguageRegistry()
        self.shebang_patterns = {
            r"#!/usr/bin/env python": "python",
            r"#!/usr/bin/python": "python",
            r"#!/bin/bash": "bash",
            r"#!/bin/sh": "shell",
            r"#!/usr/bin/env node": "javascript",
            r"#!/usr/bin/env ruby": "ruby",
            r"#!/usr/bin/env php": "php",
        }

        self.content_signatures = {
            # Python patterns
            "python": [
                r"import\s+\w+",
                r"from\s+\w+\s+import",
                r"def\s+\w+\s*\(",
                r"class\s+\w+\s*\(",
                r'if\s+__name__\s*==\s*["\']__main__["\']',
            ],
            # JavaScript/TypeScript patterns
            "javascript": [
                r"function\s+\w+\s*\(",
                r"const\s+\w+\s*=",
                r"require\s*\(",
                r"module\.exports",
                r"console\.log\s*\(",
            ],
            "typescript": [
                r"interface\s+\w+",
                r"type\s+\w+\s*=",
                r"export\s+\w+",
                r'import.*from\s+["\'].+["\']',
                r":\s*\w+\s*=",
            ],
            # Java patterns
            "java": [
                r"public\s+class\s+\w+",
                r"package\s+[\w.]+",
                r"import\s+[\w.]+",
                r"public\s+static\s+void\s+main",
                r"System\.out\.print",
            ],
            # C/C++ patterns
            "c": [
                r"#include\s*<.*>",
                r"int\s+main\s*\(",
                r"printf\s*\(",
                r"malloc\s*\(",
                r"sizeof\s*\(",
            ],
            "cpp": [
                r"#include\s*<.*>",
                r"using\s+namespace",
                r"std::",
                r"class\s+\w+",
                r"cout\s*<<",
            ],
            # Other languages
            "rust": [
                r"fn\s+\w+\s*\(",
                r"use\s+\w+",
                r"let\s+\w+\s*=",
                r"impl\s+\w+",
                r"println!\s*\(",
            ],
            "go": [
                r"package\s+\w+",
                r'import\s+["\'].*["\']',
                r"func\s+\w+\s*\(",
                r"fmt\.Print",
                r"var\s+\w+\s+\w+",
            ],
        }

    def detect_file_language(self, file_path: Path) -> Optional[LanguageConfig]:
        """Detect language of a single file using multiple methods."""

        # Method 1: File extension
        ext_result = self.registry.get_language_by_extension(file_path)
        if ext_result:
            return ext_result

        # Method 2: MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            mime_result = self._detect_by_mime_type(mime_type)
            if mime_result:
                return mime_result

        # Method 3: File content analysis
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            # Check shebang
            shebang_result = self._detect_by_shebang(content)
            if shebang_result:
                return self.registry.LANGUAGES.get(shebang_result)

            # Check content signatures
            signature_result = self._detect_by_content_signatures(content)
            if signature_result:
                return self.registry.LANGUAGES.get(signature_result)

        except OSError as e:
            logger.warning("Failed to read file %s: %s", file_path, e)

        return None

    def _detect_by_mime_type(self, mime_type: str) -> Optional[LanguageConfig]:
        """Detect language by MIME type."""
        mime_mapping = {
            "text/x-python": "python",
            "application/javascript": "javascript",
            "text/javascript": "javascript",
            "application/typescript": "typescript",
            "text/x-java-source": "java",
            "text/x-c": "c",
            "text/x-c++": "cpp",
            "text/x-rust": "rust",
            "text/x-go": "go",
            "text/html": "html",
            "text/css": "css",
            "application/json": "json",
            "text/xml": "xml",
            "text/yaml": "yaml",
        }

        lang_id = mime_mapping.get(mime_type)
        return self.registry.LANGUAGES.get(lang_id) if lang_id else None

    def _detect_by_shebang(self, content: str) -> Optional[str]:
        """Detect language by shebang line."""
        first_line = content.split("\n")[0].strip()

        for pattern, language in self.shebang_patterns.items():
            if re.match(pattern, first_line):
                return language

        return None

    def _detect_by_content_signatures(self, content: str) -> Optional[str]:
        """Detect language by content patterns."""
        scores = defaultdict(int)

        for language, patterns in self.content_signatures.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, content))
                scores[language] += matches

        if scores:
            # Return language with highest score
            return max(scores.items(), key=lambda x: x[1])[0]

        return None


class ProjectAnalyzer:  # pylint: disable=too-few-public-methods
    """Analyzes project structure and composition."""

    def __init__(self):
        self.detector = LanguageDetector()
        self.framework_indicators = {
            # JavaScript/TypeScript frameworks
            "react": ["package.json", "jsx", "tsx", "react"],
            "angular": ["angular.json", "@angular", "ng-"],
            "vue": ["vue.config.js", ".vue", "Vue"],
            "nodejs": ["package.json", "node_modules", "npm"],
            # Python frameworks
            "django": ["manage.py", "settings.py", "django"],
            "flask": ["app.py", "flask"],
            "fastapi": ["fastapi", "uvicorn"],
            # Java frameworks
            "spring": ["pom.xml", "@SpringBootApplication", "spring"],
            "maven": ["pom.xml", "src/main/java"],
            "gradle": ["build.gradle", "gradle"],
            # Build systems
            "webpack": ["webpack.config.js", "webpack"],
            "rollup": ["rollup.config.js"],
            "vite": ["vite.config.js"],
        }

        self.ci_indicators = [
            ".github/workflows",
            ".gitlab-ci.yml",
            ".travis.yml",
            "Jenkinsfile",
            ".circleci",
            "azure-pipelines.yml",
        ]

    def analyze_project(self, project_root: Path) -> ProjectProfile:
        """Analyze entire project structure and composition."""
        logger.info("Analyzing project structure at %s", project_root)

        # Scan all files
        file_analysis = self._scan_files(project_root)

        # Detect languages
        language_stats = self._analyze_languages(file_analysis)

        # Detect frameworks and build systems
        frameworks = self._detect_frameworks(project_root, file_analysis)
        build_system = self._detect_build_system(project_root)

        # Analyze project structure
        structure = self._analyze_structure(project_root, file_analysis)

        # Determine project type
        project_type = self._classify_project_type(language_stats, frameworks, structure)

        # Calculate confidence score
        confidence = self._calculate_confidence(language_stats, file_analysis)

        return ProjectProfile(
            primary_language=(
                max(language_stats.items(), key=lambda x: x[1])[0] if language_stats else "unknown"
            ),
            languages=language_stats,
            total_files=len(file_analysis),
            confidence_score=confidence,
            framework_hints=frameworks,
            build_system=build_system,
            project_type=project_type,
            source_directories=structure["source_dirs"],
            test_directories=structure["test_dirs"],
            config_files=structure["config_files"],
            has_tests=len(structure["test_dirs"]) > 0,
            has_documentation=structure["has_docs"],
            has_ci_config=structure["has_ci"],
        )

    def _scan_files(self, root: Path) -> List[Tuple[Path, Optional[LanguageConfig]]]:
        """Scan all files and detect their languages."""
        results = []
        supported_extensions = self.detector.registry.get_supported_extensions()

        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip hidden files and common ignore patterns
            if any(part.startswith(".") for part in file_path.parts):
                if not self._is_important_hidden_file(file_path):
                    continue

            # Skip common ignore directories
            if any(
                ignore_dir in file_path.parts
                for ignore_dir in ["node_modules", "__pycache__", ".git", "target", "build", "dist"]
            ):
                continue

            # Try to detect language
            lang_config = None
            if file_path.suffix.lower() in supported_extensions:
                lang_config = self.detector.detect_file_language(file_path)

            results.append((file_path, lang_config))

        return results

    def _is_important_hidden_file(self, file_path: Path) -> bool:
        """Check if hidden file is important for analysis."""
        important_files = {
            ".gitignore",
            ".dockerignore",
            ".eslintrc",
            ".prettierrc",
            ".github",
            ".gitlab-ci.yml",
            ".travis.yml",
        }
        return any(important in str(file_path) for important in important_files)

    def _analyze_languages(
        self, file_analysis: List[Tuple[Path, Optional[LanguageConfig]]]
    ) -> Dict[str, int]:
        """Analyze language distribution in the project."""
        language_counts = Counter()

        for _, lang_config in file_analysis:
            if lang_config:
                language_counts[lang_config.name.lower()] += 1

        return dict(language_counts)

    def _detect_frameworks(
        self, root: Path, file_analysis: List[Tuple[Path, Optional[LanguageConfig]]]
    ) -> List[str]:
        """Detect frameworks and libraries used in the project."""
        detected = []

        # Check for framework-specific files
        all_files = {str(f[0].relative_to(root)) for f in file_analysis}

        for framework, indicators in self.framework_indicators.items():
            if any(indicator in " ".join(all_files) for indicator in indicators):
                detected.append(framework)

        # Check package.json for JavaScript frameworks
        package_json = root / "package.json"
        if package_json.exists():
            try:
                content = json.loads(package_json.read_text())
                deps = {**content.get("dependencies", {}), **content.get("devDependencies", {})}

                for dep in deps:
                    if "react" in dep:
                        detected.append("react")
                    elif "angular" in dep:
                        detected.append("angular")
                    elif "vue" in dep:
                        detected.append("vue")

            except (OSError, json.JSONDecodeError) as e:
                logger.debug("Failed to parse package.json: %s", e)

        return list(set(detected))

    def _detect_build_system(self, root: Path) -> Optional[str]:
        """Detect the primary build system."""
        build_indicators = [
            ("package.json", "npm"),
            ("yarn.lock", "yarn"),
            ("pom.xml", "maven"),
            ("build.gradle", "gradle"),
            ("Cargo.toml", "cargo"),
            ("pyproject.toml", "python-build"),
            ("setup.py", "setuptools"),
            ("Makefile", "make"),
            ("CMakeLists.txt", "cmake"),
        ]

        for filename, build_system in build_indicators:
            if (root / filename).exists():
                return build_system

        return None

    def _analyze_structure(
        self, root: Path, file_analysis: List[Tuple[Path, Optional[LanguageConfig]]]
    ) -> Dict[str, Any]:
        """Analyze project directory structure."""
        source_dirs = set()
        test_dirs = set()
        config_files = []
        has_docs = False
        has_ci = False

        for file_path, lang_config in file_analysis:
            rel_path = file_path.relative_to(root)

            # Identify source directories
            if lang_config and len(rel_path.parts) > 1:
                potential_source_dir = rel_path.parts[0]
                if potential_source_dir in ["src", "lib", "app", "source"]:
                    source_dirs.add(root / potential_source_dir)

            # Identify test directories
            if any(
                test_indicator in str(rel_path).lower()
                for test_indicator in ["test", "tests", "spec", "specs", "__tests__"]
            ):
                test_dirs.add(file_path.parent)

            # Identify config files
            if file_path.suffix in [".json", ".yml", ".yaml", ".toml", ".ini", ".cfg"]:
                config_files.append(file_path)

            # Check for documentation
            if any(
                doc_indicator in str(rel_path).lower()
                for doc_indicator in ["readme", "doc", "docs", "documentation"]
            ):
                has_docs = True

            # Check for CI configuration
            if any(ci_indicator in str(rel_path) for ci_indicator in self.ci_indicators):
                has_ci = True

        return {
            "source_dirs": list(source_dirs),
            "test_dirs": list(test_dirs),
            "config_files": config_files,
            "has_docs": has_docs,
            "has_ci": has_ci,
        }

    def _classify_project_type(
        self, languages: Dict[str, int], frameworks: List[str], structure: Dict[str, Any]
    ) -> str:
        """Classify the type of project."""

        # Web application indicators
        if any(fw in frameworks for fw in ["react", "angular", "vue", "django", "flask"]):
            return "web_application"

        # Mobile application indicators
        if "swift" in languages or "dart" in languages:
            return "mobile_application"

        # System/CLI tool indicators
        if any(lang in languages for lang in ["rust", "go", "c", "cpp"]):
            return "system_tool"

        # Library/SDK indicators
        if any(build in frameworks for build in ["maven", "gradle", "cargo", "npm"]):
            if len(structure["source_dirs"]) > 0 and not frameworks:
                return "library"

        # Data/ML project indicators
        if "python" in languages and any(
            config.name.endswith(".ipynb") for config in structure["config_files"]
        ):
            return "data_science"

        # Default classification
        primary_lang = max(languages.items(), key=lambda x: x[1])[0] if languages else "unknown"
        return f"{primary_lang}_project"

    def _calculate_confidence(
        self, languages: Dict[str, int], file_analysis: List[Tuple[Path, Optional[LanguageConfig]]]
    ) -> float:
        """Calculate confidence score for the analysis."""
        total_files = len(file_analysis)
        identified_files = sum(languages.values())

        if total_files == 0:
            return 0.0

        # Base confidence from identification rate
        identification_rate = identified_files / total_files

        # Boost confidence if there's a clear primary language
        if languages:
            max_lang_files = max(languages.values())
            dominance = max_lang_files / identified_files if identified_files > 0 else 0
            confidence = (identification_rate * 0.7) + (dominance * 0.3)
        else:
            confidence = identification_rate

        return min(confidence, 1.0)


class LanguageRouter:
    """Routes files and analysis tasks to appropriate language-specific handlers."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.analyzer = ProjectAnalyzer()
        self.project_profile: Optional[ProjectProfile] = None

    def initialize_project(self) -> ProjectProfile:
        """Initialize and analyze the project structure."""
        self.project_profile = self.analyzer.analyze_project(self.project_root)

        logger.info("Project analysis complete:")
        logger.info("  Primary language: %s", self.project_profile.primary_language)
        logger.info("  Total files: %d", self.project_profile.total_files)
        logger.info("  Languages: %s", dict(self.project_profile.languages))
        logger.info("  Confidence: %.2f", self.project_profile.confidence_score)

        return self.project_profile

    def get_analysis_priority(self) -> List[str]:
        """Get ordered list of languages by analysis priority."""
        if not self.project_profile:
            self.initialize_project()

        # Sort languages by file count (descending)
        return sorted(self.project_profile.languages.items(), key=lambda x: x[1], reverse=True)

    def should_analyze_file(self, file_path: Path) -> bool:
        """Determine if a file should be included in analysis."""
        if not self.project_profile:
            self.initialize_project()

        # Check if file is in a test directory (may want to skip or analyze separately)
        for test_dir in self.project_profile.test_directories:
            if test_dir in file_path.parents:
                return True  # Include tests but mark them as such

        # Check if file is in a source directory
        for source_dir in self.project_profile.source_directories:
            if source_dir in file_path.parents:
                return True

        # Check if file has a supported language
        lang_config = self.analyzer.detector.detect_file_language(file_path)
        return lang_config is not None

    def get_routing_strategy(self) -> Dict[str, Any]:
        """Get optimal routing strategy for the project."""
        if not self.project_profile:
            self.initialize_project()

        return {
            "primary_language": self.project_profile.primary_language,
            "multi_language": len(self.project_profile.languages) > 1,
            "analysis_order": self.get_analysis_priority(),
            "parallel_processing": len(self.project_profile.languages) > 2,
            "framework_optimizations": self.project_profile.framework_hints,
            "project_type": self.project_profile.project_type,
        }
