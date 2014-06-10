django-debug-toolbar-openstack-panel
====================================

A django-debug-toolbar panel for OpenStack Dashboard

Installation
============

``pip install git+https://github.com/andriyko/django-debug-toolbar-openstack-panel.git``

Setup
=====
Add the following lines to your ``settings.py``:

    INSTALLED_APPS = (
        ...
        'openstack_panel',
        ...
    )
    DEBUG_TOOLBAR_PANELS = (
        ...
        'openstack_panel.panels.openstack.OpenstackPanel',
        ...
    )

An extra panel titled "OpenStack" should appear in debug toolbar.

An example of panel configuration in ``settings.py``:

    DEBUG_TOOLBAR_OPENSTACK_PANEL = {
        'OPENSTACK_CLIENTS_LIST': ('ceilometerclient', 'cinderclient',
                                   'glanceclient','heatclient',
                                   'keystoneclient', 'neutronclient',
                                   'novaclient', 'swiftclient', 'troveclient', ),
        'OPENSTACK_OTHERS_LIST': ('horizon', 'openstack_dashboard', ),
        'TRACE_STACK': True,
    }
