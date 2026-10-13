// Fictional raw errors from "Tallyboard", a made-up team task tracking app.
export const RAW_ERRORS: string[] = [
  "TypeError: Cannot read properties of undefined (reading 'assigneeId') at TaskCard.render (src/components/TaskCard.tsx:84:31) at renderWithHooks (react-dom.development.js:14985)",
  "Error: connect ECONNREFUSED 10.4.2.17:5432 at TCPConnectWrap.afterConnect [as oncomplete] (node:net:1555:16) - pool 'boards-db' exhausted",
  "HTTP 413 PayloadTooLargeError: request entity too large (limit 10485760, received 24117248) at POST /api/v2/attachments/upload",
  "ValidationError: field 'dueDate' failed constraint iso8601_future_date: value '2021-03-09' is in the past (board_id=brd_88f1, task_id=tsk_20931)",
  "ForbiddenError: 403 user usr_5521 lacks permission 'board:archive' on workspace wsp_acme-design at AuthGuard.canActivate (auth.guard.ts:42)",
];
