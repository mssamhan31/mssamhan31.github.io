"""Static site generator for mssamhan31.github.io.

Modules:
    privacy  - patterns that must never appear on the public site; shared by sync, import and tests
    cv_data  - loads data/cv.json and applies the grouping, merging and sorting rules per CV section
    images   - resizes photos to web size
    render   - renders every page from the Jinja2 templates
"""
