// Copyright 2026. Fog of War chess engine.
//
// A dependency-free test harness. The course build runs offline, so the engine
// cannot rely on an external framework; this provides just enough to write
// readable assertions and get a useful failure report.

#ifndef FOW_TESTS_TESTING_H_
#define FOW_TESTS_TESTING_H_

#include <cstdio>
#include <string>
#include <type_traits>

namespace fow::testing {

struct Results {
  int checks = 0;
  int failures = 0;
  std::string current_test;
};

inline Results& State() {
  static Results results;
  return results;
}

inline void Report(const char* file, int line, const char* expression) {
  Results& state = State();
  ++state.failures;
  std::fprintf(stderr, "  FAIL %s:%d in %s\n       %s\n", file, line,
               state.current_test.c_str(), expression);
}

inline int Summarize(const char* suite) {
  const Results& state = State();
  std::fprintf(stderr, "%s: %d checks, %d failures\n", suite, state.checks,
               state.failures);
  return state.failures == 0 ? 0 : 1;
}

// Renders a value for a failure message when it is something std::to_string
// understands, so the macros work for pointers and enums too.
template <typename T>
std::string Describe(const T& value) {
  if constexpr (std::is_arithmetic_v<T>) {
    return std::to_string(value);
  } else if constexpr (std::is_enum_v<T>) {
    return std::to_string(static_cast<long long>(value));
  } else if constexpr (std::is_convertible_v<T, std::string>) {
    return std::string(value);
  } else {
    return "<value>";
  }
}

}  // namespace fow::testing

#define FOW_EXPECT_TRUE(condition)                                       \
  do {                                                                   \
    ++::fow::testing::State().checks;                                    \
    if (!(condition)) {                                                  \
      ::fow::testing::Report(__FILE__, __LINE__, #condition);            \
    }                                                                    \
  } while (false)

#define FOW_EXPECT_EQ(actual, expected)                                       \
  do {                                                                        \
    ++::fow::testing::State().checks;                                         \
    const auto fow_actual = (actual);                                         \
    const auto fow_expected = (expected);                                     \
    if (!(fow_actual == fow_expected)) {                                      \
      ::fow::testing::Report(                                                 \
          __FILE__, __LINE__,                                                 \
          (std::string(#actual " == " #expected) + " [actual=" +              \
           ::fow::testing::Describe(fow_actual) + " expected=" +              \
           ::fow::testing::Describe(fow_expected) + "]")                      \
              .c_str());                                                      \
    }                                                                         \
  } while (false)

#define FOW_RUN_TEST(function)                        \
  do {                                                \
    ::fow::testing::State().current_test = #function; \
    function();                                       \
  } while (false)

#endif  // FOW_TESTS_TESTING_H_
