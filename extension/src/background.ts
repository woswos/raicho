import { startManagedConnector, type ManagedApi } from './managed_connector.js';

declare const messenger: ManagedApi;

startManagedConnector(messenger);
