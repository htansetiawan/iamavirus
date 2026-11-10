/* Diagnostic only: observe the unchanged UCI startup, without reaping a child,
 * consuming additional engine output, changing a deadline, or retrying it. */
static int astra_startup_active, astra_startup_lines;
static const char *astra_startup_phase = "none";
static double astra_startup_begin;

static void astra_startup_event(Worker *w, const char *event,
                                const char *line, int inspect_child) {
    const int saved_errno = errno;
    if (!astra_startup_active || !getenv("ASTRA_SF_STARTUP_TRACE")) return;
    siginfo_t info;
    memset(&info, 0, sizeof info);
    int observed = 0, observed_errno = 0;
    if (inspect_child && w->child > 0) {
        observed = waitid(P_PID, (id_t)w->child, &info,
                          WEXITED | WNOHANG | WNOWAIT);
        observed_errno = observed < 0 ? errno : 0;
    }
    char hex[513];
    size_t length = line ? strlen(line) : 0;
    const size_t take = length < 256 ? length : 256;
    static const char digits[] = "0123456789abcdef";
    for (size_t i = 0; i < take; ++i) {
        const unsigned char c = (unsigned char)line[i];
        hex[2*i] = digits[c >> 4]; hex[2*i+1] = digits[c & 15];
    }
    hex[2*take] = 0;
    fprintf(stderr, "astra-sf-startup {\"event\":\"%s\",\"phase\":\"%s\","
        "\"worker\":%ld,\"child\":%ld,\"elapsed_ms\":%.6f,\"errno\":%d,"
        "\"inspected_child\":%d,\"waitid_return\":%d,\"waitid_errno\":%d,"
        "\"exited_pid\":%ld,\"exit_code_kind\":%d,\"exit_status\":%d,"
        "\"buffered_bytes\":%zu,\"line_length\":%zu,\"line_hex\":\"%s\"}\n",
        event, astra_startup_phase, (long)(w-workers), (long)w->child,
        1000*(now()-astra_startup_begin), saved_errno, inspect_child,
        observed, observed_errno, (long)info.si_pid, info.si_code,
        info.si_status, w->have-w->start, length, hex);
    errno = saved_errno;
}
