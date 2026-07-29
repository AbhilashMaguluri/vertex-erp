"""Office Import — turns the spreadsheet the college office already keeps into
provisioned Student and Counsellor accounts.

The module deliberately holds no UUIDs, no ID columns and no bespoke CSV
template: the administrator uploads the file as received and everything else
(roll-range expansion, counsellor de-duplication, account creation, counsellor
assignment, credential generation) is derived.
"""
