// Tests that spawn processes run apart, because a child briefly inherits every open lock.

mod credential_cli;
mod credential_file_safety;
mod login_cli;
mod server_process;
