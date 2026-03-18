<?php
/**
 * Active Directory - Locked Accounts API
 * --------------------------------------
 * Returns a JSON list of locked AD accounts with lock duration.
 *
 * Requirements:
 * - PHP LDAP extension enabled
 * - A valid LDAP connection file (see ldap_config.php)
 */

header('Content-Type: application/json');

// 👉 External LDAP connection config
$ldap_conn = include('ldap_config.php');

// 👉 LDAP filter for locked accounts
$filter = "(&(objectCategory=person)(objectClass=user)(lockoutTime>=1)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))";

// 👉 Base DN (TO ADAPT TO YOUR ENVIRONMENT)
$base_dn = "OU=YOUR_ORG_UNIT,DC=example,DC=local";

// 👉 LDAP query
$search = ldap_search($ldap_conn, $base_dn, $filter, ['samaccountname','lockoutTime']);
$entries = ldap_get_entries($ldap_conn, $search);

ldap_unbind($ldap_conn);

/**
 * Convert Windows timestamp (AD) to Unix timestamp
 */
function win_to_unix($ts) {
    if (!$ts || $ts == 0) return 0;
    return ($ts / 10000000) - 11644473600;
}

$locked = [];

if ($entries['count'] > 0) {
    for ($i = 0; $i < $entries['count']; $i++) {
        if (!empty($entries[$i]['samaccountname'][0])) {

            $lockTime = $entries[$i]['lockouttime'][0] ?? 0;

            $locked[] = [
                "user" => $entries[$i]['samaccountname'][0],
                "lock_time" => win_to_unix($lockTime)
            ];
        }
    }
}

// 👉 JSON output
echo json_encode([
    "count" => count($locked),
    "users" => $locked
]);
