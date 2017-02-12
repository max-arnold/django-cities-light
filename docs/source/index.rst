.. include:: ../../README.rst

Contents:

.. toctree::
   :maxdepth: 2

   database
   full
   contrib

FAQ
===

Supported RDBMS
---------------

The only supported RDBMS is PostgreSQL.

Some data fail to import, how to skip them ?
--------------------------------------------

GeoNames is not perfect and there might be some edge cases from time to time.
We want the ``cities_light`` management command to work for everybody so you
should `open an issue in GitHub
<https://github.com/yourlabs/django-cities-light/issues?state=open>`_ if you
get a crash from that command.

However, we don't want you to be blocked, so keep in mind that you can use
:ref:`signals` like :py:data:`cities_light.city_items_pre_import
<cities_light.signals.city_items_pre_import>`,
:py:data:`cities_light.region_items_pre_import
<cities_light.signals.region_items_pre_import>`,
:py:data:`cities_light.country_items_pre_import
<cities_light.signals.country_items_pre_import>`, to skip or fix items before
they get inserted in the database by the normal process.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
