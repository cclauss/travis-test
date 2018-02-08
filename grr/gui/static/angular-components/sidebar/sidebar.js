'use strict';

goog.provide('grrUi.sidebar');
goog.provide('grrUi.sidebar.sidebarModule');
goog.require('grrUi.sidebar.clientSummaryDirective');  // USE: ClientSummaryDirective
goog.require('grrUi.sidebar.navDropdownDirective');  // USE: NavDropdownDirective
goog.require('grrUi.sidebar.navLinkDirective');      // USE: NavLinkDirective
goog.require('grrUi.sidebar.navigatorDirective');    // USE: NavigatorDirective

/**
 * Angular module for layout-related UI.
 */
grrUi.sidebar.sidebarModule = angular.module('grrUi.sidebar', []);

grrUi.sidebar.sidebarModule.directive(
    grrUi.sidebar.clientSummaryDirective.ClientSummaryDirective.directive_name,
    grrUi.sidebar.clientSummaryDirective.ClientSummaryDirective);
grrUi.sidebar.sidebarModule.directive(
    grrUi.sidebar.navDropdownDirective.NavDropdownDirective.directive_name,
    grrUi.sidebar.navDropdownDirective.NavDropdownDirective);
grrUi.sidebar.sidebarModule.directive(
    grrUi.sidebar.navLinkDirective.NavLinkDirective.directive_name,
    grrUi.sidebar.navLinkDirective.NavLinkDirective);
grrUi.sidebar.sidebarModule.directive(
    grrUi.sidebar.navigatorDirective.NavigatorDirective.directive_name,
    grrUi.sidebar.navigatorDirective.NavigatorDirective);