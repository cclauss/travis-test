goog.provide('grrUi.acl');
goog.provide('grrUi.acl.aclModule');
goog.require('grrUi.acl.aclDialogService');       // USE: AclDialogService
goog.require('grrUi.acl.approvalInfoDirective');  // USE: ApprovalInfoDirective
goog.require('grrUi.acl.clientApprovalViewDirective');  // USE: ClientApprovalViewDirective
goog.require('grrUi.acl.cronJobApprovalViewDirective');  // USE: CronJobApprovalViewDirective
goog.require('grrUi.acl.huntApprovalViewDirective');  // USE: HuntApprovalViewDirective
goog.require('grrUi.acl.huntFromFlowCopyReviewDirective');  // USE: HuntFromFlowCopyReviewDirective
goog.require('grrUi.acl.huntFromHuntCopyReviewDirective');  // USE: HuntFromHuntCopyReviewDirective
goog.require('grrUi.acl.requestApprovalDialogDirective');  // USE: RequestApprovalDialogDirective
goog.require('grrUi.core.apiService');  // USE: UNAUTHORIZED_API_RESPONSE_EVENT

/**
 * Angular module for acl GRR UI components.
 */
grrUi.acl.aclModule = angular.module('grrUi.acl', ['grrUi.core']);

grrUi.acl.aclModule.service(
    grrUi.acl.aclDialogService.AclDialogService.service_name,
    grrUi.acl.aclDialogService.AclDialogService);

grrUi.acl.aclModule.directive(
    grrUi.acl.approvalInfoDirective.ApprovalInfoDirective.directive_name,
    grrUi.acl.approvalInfoDirective.ApprovalInfoDirective);
grrUi.acl.aclModule.directive(
    grrUi.acl.clientApprovalViewDirective.ClientApprovalViewDirective.directive_name,
    grrUi.acl.clientApprovalViewDirective.ClientApprovalViewDirective);
grrUi.acl.aclModule.directive(
    grrUi.acl.cronJobApprovalViewDirective.CronJobApprovalViewDirective.directive_name,
    grrUi.acl.cronJobApprovalViewDirective.CronJobApprovalViewDirective);
grrUi.acl.aclModule.directive(
    grrUi.acl.huntApprovalViewDirective.HuntApprovalViewDirective.directive_name,
    grrUi.acl.huntApprovalViewDirective.HuntApprovalViewDirective);
grrUi.acl.aclModule.directive(
    grrUi.acl.huntFromFlowCopyReviewDirective.HuntFromFlowCopyReviewDirective.directive_name,
    grrUi.acl.huntFromFlowCopyReviewDirective.HuntFromFlowCopyReviewDirective);
grrUi.acl.aclModule.directive(
    grrUi.acl.huntFromHuntCopyReviewDirective.HuntFromHuntCopyReviewDirective.directive_name,
    grrUi.acl.huntFromHuntCopyReviewDirective.HuntFromHuntCopyReviewDirective);
grrUi.acl.aclModule.directive(
    grrUi.acl.requestApprovalDialogDirective.RequestApprovalDialogDirective.directive_name,
    grrUi.acl.requestApprovalDialogDirective.RequestApprovalDialogDirective);

grrUi.acl.aclModule.run(function($rootScope, grrAclDialogService) {
  var UNAUTHORIZED_API_RESPONSE_EVENT =
      grrUi.core.apiService.UNAUTHORIZED_API_RESPONSE_EVENT;

  // Listen to UnauthorizedApiResponse events and show the approval
  // dialog when they're fired (see core/api-service.js for the
  // source of the events).
  $rootScope.$on(UNAUTHORIZED_API_RESPONSE_EVENT, function(event, data) {
    grrAclDialogService.openApprovalDialogForSubject(data['subject'], data['reason']);
  });
});
