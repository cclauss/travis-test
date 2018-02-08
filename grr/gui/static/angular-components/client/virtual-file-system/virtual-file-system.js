'use strict';

goog.provide('grrUi.client.virtualFileSystem');
goog.provide('grrUi.client.virtualFileSystem.virtualFileSystemModule');

goog.require('grrUi.client.virtualFileSystem.breadcrumbsDirective');  // USE: BreadcrumbsDirective
goog.require('grrUi.client.virtualFileSystem.encodingsDropdownDirective');  // USE: EncodingsDropdownDirective
goog.require('grrUi.client.virtualFileSystem.fileContextDirective');  // USE: FileContextDirective
goog.require('grrUi.client.virtualFileSystem.fileDetailsDirective');  // USE: FileDetailsDirective
goog.require('grrUi.client.virtualFileSystem.fileDownloadViewDirective');  // USE: FileDownloadViewDirective
goog.require('grrUi.client.virtualFileSystem.fileHexViewDirective');  // USE: FileHexViewDirective
goog.require('grrUi.client.virtualFileSystem.fileStatsViewDirective');  // USE: FileStatsViewDirective
goog.require('grrUi.client.virtualFileSystem.fileTableDirective');  // USE: FileTableDirective
goog.require('grrUi.client.virtualFileSystem.fileTextViewDirective');  // USE: FileTextViewDirective
goog.require('grrUi.client.virtualFileSystem.fileTimelineDirective');  // USE: FileTimelineDirective
goog.require('grrUi.client.virtualFileSystem.fileTreeDirective');  // USE: FileTreeDirective
goog.require('grrUi.client.virtualFileSystem.fileViewDirective');  // USE: FileViewDirective
goog.require('grrUi.client.virtualFileSystem.rWeOwnedButtonDirective');  // USE: RWeOwnedButtonDirective
goog.require('grrUi.client.virtualFileSystem.recursiveListButtonDirective');  // USE: RecursiveListButtonDirective
goog.require('grrUi.client.virtualFileSystem.vfsFilesArchiveButtonDirective');  // USE: VfsFilesArchiveButtonDirective
goog.require('grrUi.core');      // USE: coreModule
goog.require('grrUi.semantic');  // USE: semanticModule


/**
 * Angular module for clients-related UI.
 */
grrUi.client.virtualFileSystem.virtualFileSystemModule = angular.module('grrUi.client.virtualFileSystem',
                                                       [grrUi.core.coreModule.name,
                                                        grrUi.semantic.semanticModule.name]);

grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.breadcrumbsDirective.BreadcrumbsDirective.directive_name,
    grrUi.client.virtualFileSystem.breadcrumbsDirective.BreadcrumbsDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.encodingsDropdownDirective.EncodingsDropdownDirective.directive_name,
    grrUi.client.virtualFileSystem.encodingsDropdownDirective.EncodingsDropdownDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.fileContextDirective.FileContextDirective.directive_name,
    grrUi.client.virtualFileSystem.fileContextDirective.FileContextDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.fileDetailsDirective.FileDetailsDirective.directive_name,
    grrUi.client.virtualFileSystem.fileDetailsDirective.FileDetailsDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.fileDownloadViewDirective.FileDownloadViewDirective.directive_name,
    grrUi.client.virtualFileSystem.fileDownloadViewDirective.FileDownloadViewDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.fileHexViewDirective.FileHexViewDirective.directive_name,
    grrUi.client.virtualFileSystem.fileHexViewDirective.FileHexViewDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.fileStatsViewDirective.FileStatsViewDirective.directive_name,
    grrUi.client.virtualFileSystem.fileStatsViewDirective.FileStatsViewDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.fileTableDirective.FileTableDirective.directive_name,
    grrUi.client.virtualFileSystem.fileTableDirective.FileTableDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.fileTimelineDirective.FileTimelineDirective.directive_name,
    grrUi.client.virtualFileSystem.fileTimelineDirective.FileTimelineDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.fileTextViewDirective.FileTextViewDirective.directive_name,
    grrUi.client.virtualFileSystem.fileTextViewDirective.FileTextViewDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.fileTreeDirective.FileTreeDirective.directive_name,
    grrUi.client.virtualFileSystem.fileTreeDirective.FileTreeDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.fileViewDirective.FileViewDirective.directive_name,
    grrUi.client.virtualFileSystem.fileViewDirective.FileViewDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.recursiveListButtonDirective.RecursiveListButtonDirective.directive_name,
    grrUi.client.virtualFileSystem.recursiveListButtonDirective.RecursiveListButtonDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.vfsFilesArchiveButtonDirective.VfsFilesArchiveButtonDirective.directive_name,
    grrUi.client.virtualFileSystem.vfsFilesArchiveButtonDirective.VfsFilesArchiveButtonDirective);
grrUi.client.virtualFileSystem.virtualFileSystemModule.directive(
    grrUi.client.virtualFileSystem.rWeOwnedButtonDirective.RWeOwnedButtonDirective.directive_name,
    grrUi.client.virtualFileSystem.rWeOwnedButtonDirective.RWeOwnedButtonDirective);
