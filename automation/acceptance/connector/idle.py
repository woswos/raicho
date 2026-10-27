import time

from automation.acceptance.connector.status import status


def observe_idle(seconds=600, sample=status, clock=time.monotonic, pause=time.sleep, report=print):
    started = clock()
    baseline = sample()
    generation = baseline['generation']
    assert baseline['status'] == 'connected' and generation, 'Connector is not active'
    previous = baseline['heartbeat_count']
    assert type(previous) is int and previous > 0, 'Connector has no heartbeat'
    progressed = started
    next_report = 60
    while True:
        elapsed = clock() - started
        if elapsed >= seconds:
            break
        pause(min(15, seconds - elapsed))
        backend = sample()
        assert backend['status'] == 'connected', 'Connector disconnected during idle'
        assert backend['generation'] == generation, 'Connector session changed during idle'
        count = backend['heartbeat_count']
        assert type(count) is int and count >= previous, 'Heartbeat counter reset'
        now = clock()
        if count > previous:
            progressed = now
        assert now - progressed <= 45, 'Connector heartbeat stopped during idle'
        previous = count
        elapsed = now - started
        if elapsed >= next_report:
            report(
                f'Idle acceptance: {int(elapsed)} seconds, heartbeat {count}',
                flush=True,
            )
            next_report += 60
    assert previous > baseline['heartbeat_count'], 'Connector heartbeat did not advance'
    report('Production connector passed ten-minute idle acceptance', flush=True)
