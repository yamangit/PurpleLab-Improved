<?php

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$input = file_get_contents('php://input');
$payload = json_decode($input, true);
$action = $payload['action'] ?? '';

$action_map = [
    'restore' => '/restore_snapshot',
    'poweroff' => '/poweroff_vm',
    'start' => '/start_vm_headless',
    'reboot' => '/reboot_vm',
    'snapshot' => '/take_snapshot'
];

if (!isset($action_map[$action])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid action']);
    exit;
}

$endpoint = 'http://127.0.0.1:5000' . $action_map[$action];
$ch = curl_init($endpoint);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 2);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);

if ($response === false) {
    $error_message = curl_error($ch);
    curl_close($ch);
    http_response_code(502);
    echo json_encode(['error' => 'Backend request failed', 'details' => $error_message]);
    exit;
}

curl_close($ch);

if ($http_code) {
    http_response_code($http_code);
} else {
    http_response_code(500);
}

echo $response;
