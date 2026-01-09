/**
 * Scan Queue Manager
 * 
 * Limits concurrent repository scans to prevent server overload.
 * Uses in-memory queue with per-organization limits.
 */

interface QueuedScan {
    id: string;
    repositoryId: string;
    organizationId: string;
    status: 'queued' | 'processing' | 'completed' | 'failed';
    queuedAt: Date;
    startedAt?: Date;
    completedAt?: Date;
    error?: string;
    resolve?: (value: void) => void;
    reject?: (error: Error) => void;
}

// Configuration
const MAX_CONCURRENT_SCANS_GLOBAL = 5;
const MAX_CONCURRENT_SCANS_PER_ORG = 2;
const SCAN_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

// State
const scanQueue: Map<string, QueuedScan> = new Map();
let activeScansGlobal = 0;
const activeScansPerOrg: Map<string, number> = new Map();

/**
 * Generate unique scan ID
 */
function generateScanId(): string {
    return `scan_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Get queue statistics
 */
export function getQueueStats() {
    const scans = Array.from(scanQueue.values());
    return {
        pending: scans.filter(s => s.status === 'queued').length,
        processing: scans.filter(s => s.status === 'processing').length,
        completed: scans.filter(s => s.status === 'completed').length,
        failed: scans.filter(s => s.status === 'failed').length,
        total: scans.length,
        activeGlobal: activeScansGlobal,
        maxGlobal: MAX_CONCURRENT_SCANS_GLOBAL,
        maxPerOrg: MAX_CONCURRENT_SCANS_PER_ORG
    };
}

/**
 * Check if organization can start a new scan
 */
function canStartScan(organizationId: string): boolean {
    if (activeScansGlobal >= MAX_CONCURRENT_SCANS_GLOBAL) {
        return false;
    }

    const orgScans = activeScansPerOrg.get(organizationId) || 0;
    if (orgScans >= MAX_CONCURRENT_SCANS_PER_ORG) {
        return false;
    }

    return true;
}

/**
 * Process next queued scan if capacity allows
 */
function processNextInQueue() {
    // Find next queued scan that can be started
    for (const [id, scan] of scanQueue) {
        if (scan.status === 'queued' && canStartScan(scan.organizationId)) {
            startScan(scan);
            break;
        }
    }
}

/**
 * Start processing a scan
 */
function startScan(scan: QueuedScan) {
    scan.status = 'processing';
    scan.startedAt = new Date();

    activeScansGlobal++;
    const orgScans = activeScansPerOrg.get(scan.organizationId) || 0;
    activeScansPerOrg.set(scan.organizationId, orgScans + 1);

    // Set timeout for scan
    setTimeout(() => {
        if (scan.status === 'processing') {
            completeScan(scan.id, false, 'Scan timeout exceeded');
        }
    }, SCAN_TIMEOUT_MS);

    // Resolve the promise to allow the actual scan to proceed
    if (scan.resolve) {
        scan.resolve();
    }
}

/**
 * Queue a new scan request
 * Returns a promise that resolves when the scan can start
 */
export function queueScan(repositoryId: string, organizationId: string): Promise<string> {
    const scanId = generateScanId();

    return new Promise((resolve, reject) => {
        const scan: QueuedScan = {
            id: scanId,
            repositoryId,
            organizationId,
            status: 'queued',
            queuedAt: new Date(),
            resolve: () => resolve(scanId),
            reject
        };

        scanQueue.set(scanId, scan);

        // Try to start immediately if capacity allows
        if (canStartScan(organizationId)) {
            startScan(scan);
        }
        // Otherwise, it will be processed when capacity frees up
    });
}

/**
 * Mark a scan as completed
 */
export function completeScan(scanId: string, success: boolean, error?: string) {
    const scan = scanQueue.get(scanId);
    if (!scan) return;

    scan.status = success ? 'completed' : 'failed';
    scan.completedAt = new Date();
    if (error) scan.error = error;

    // Free up capacity (only if scan had actually started processing)
    if (scan.startedAt) {
        activeScansGlobal = Math.max(0, activeScansGlobal - 1);
        const orgScans = activeScansPerOrg.get(scan.organizationId) || 1;
        activeScansPerOrg.set(scan.organizationId, Math.max(0, orgScans - 1));
    }

    // If scan failed and had a reject callback
    if (!success && scan.reject && error) {
        scan.reject(new Error(error));
    }

    // Clean up old completed scans (keep last 100)
    const allScans = Array.from(scanQueue.entries());
    const completedScans = allScans.filter(([_, s]) =>
        s.status === 'completed' || s.status === 'failed'
    );
    if (completedScans.length > 100) {
        const toRemove = completedScans.slice(0, completedScans.length - 100);
        toRemove.forEach(([id]) => scanQueue.delete(id));
    }

    // Try to process next queued item
    processNextInQueue();
}

/**
 * Get position in queue for a scan
 */
export function getQueuePosition(scanId: string): number | null {
    const scans = Array.from(scanQueue.values());
    const queuedScans = scans.filter(s => s.status === 'queued');
    const index = queuedScans.findIndex(s => s.id === scanId);
    return index >= 0 ? index + 1 : null;
}

/**
 * Check if a repository already has an active scan
 */
export function hasActiveScan(repositoryId: string): boolean {
    for (const scan of scanQueue.values()) {
        if (scan.repositoryId === repositoryId &&
            (scan.status === 'queued' || scan.status === 'processing')) {
            return true;
        }
    }
    return false;
}

export default {
    queueScan,
    completeScan,
    getQueueStats,
    getQueuePosition,
    hasActiveScan
};
