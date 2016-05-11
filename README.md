# Nipyper

Nipyper is a Flask-based RESTful service for creating, executing, and monitoring [Nipype](http://nipy.org/nipype/) workflows.

### Usage

Documentation is coming soon

### Known Issues/TODOs

- `MapNode` execution doesn't work due to a pickling issue. I'm investigating this.
- `chroot` jailing the execution plugin isn't actually useful, since the code is being executed by Celery workers which aren't necessarily jailed. I'll have to use a different isolation scheme.