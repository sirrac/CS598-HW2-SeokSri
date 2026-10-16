#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <node.h>

namespace genetic {
namespace detail {

static constexpr float MIN_VAL = 0.001f;

inline bool is_terminal(node::type t) {
  return t == node::type::variable || t == node::type::constant;
}

inline bool is_nonterminal(node::type t) { return !is_terminal(t); }

inline int arity(node::type t) {
  if (node::type::unary_begin <= t && t <= node::type::unary_end) {
    return 1;
  }
  if (node::type::binary_begin <= t && t <= node::type::binary_end) {
    return 2;
  }
  return 0;
}

// `data` assumed to be stored in col-major format
inline float evaluate_node(const node &n, const float *data, const uint64_t stride,
                    const uint64_t idx, const float *in) {
  if (n.t == node::type::constant) {
    return n.u.val;
  } else if (n.t == node::type::variable) {
    return data[(stride * n.u.fid) + idx];
  } else {
    auto abs_inval = fabsf(in[0]), abs_inval1 = fabsf(in[1]);
    // note: keep the case statements in alphabetical order under each category
    // of operators.
    switch (n.t) {
    // binary operators
    case node::type::add:
      return in[0] + in[1];
    case node::type::atan2:
      return atan2f(in[0], in[1]);
    case node::type::div:
      return abs_inval1 < MIN_VAL ? 1.0f : (in[0]/in[1]);//fdividef(in[0], in[1]);
    case node::type::fdim:
      return fdimf(in[0], in[1]);
    case node::type::gt:
      return in[0] > in[1] ? 1.0f : 0.0f;
    case node::type::max:
      return fmaxf(in[0], in[1]);
    case node::type::min:
      return fminf(in[0], in[1]);
    case node::type::mul:
      return in[0] * in[1];
    case node::type::pow:
      return powf(in[0], in[1]);
    case node::type::sub:
      return in[0] - in[1];
    // unary operators
    case node::type::abs:
      return abs_inval;
    case node::type::acos:
      return acosf(in[0]);
    case node::type::acosh:
      return acoshf(in[0]);
    case node::type::asin:
      return asinf(in[0]);
    case node::type::asinh:
      return asinhf(in[0]);
    case node::type::atan:
      return atanf(in[0]);
    case node::type::atanh:
      return atanhf(in[0]);
    case node::type::cbrt:
      return cbrtf(in[0]);
    case node::type::cos:
      return cosf(in[0]);
    case node::type::cosh:
      return coshf(in[0]);
    case node::type::cube:
      return in[0] * in[0] * in[0];
    case node::type::exp:
      return expf(in[0]);
    case node::type::inv:
      return abs_inval < MIN_VAL ? 0.f : 1.f / in[0];
    case node::type::log:
      return abs_inval < MIN_VAL ? 0.f : logf(abs_inval);
    case node::type::neg:
      return -in[0];
    case node::type::rcbrt:
      return static_cast<float>(1.0) / cbrtf(in[0]);
    case node::type::rsqrt:
      return static_cast<float>(1.0) / sqrtf(abs_inval);
    case node::type::sin:
      return sinf(in[0]);
    case node::type::sinh:
      return sinhf(in[0]);
    case node::type::sq:
      return in[0] * in[0];
    case node::type::sqrt:
      return sqrtf(abs_inval);
    case node::type::tan:
      return tanf(in[0]);
    case node::type::tanh:
      return tanhf(in[0]);
    // shouldn't reach here!
    default:
      return 0.f;
    };
  }
}

// Same as evaluate_node, but for all `stride` rows at once: `in[0][idx]` and
// `in[1][idx]` are the operands of row `idx`, and its result is written to
// `out[idx]`. The operation is selected once; each case below gets its own
// loop with the operation inlined.
// `data` assumed to be stored in col-major format
inline void evaluate_node_column(const node &n, const float *data,
                                 const uint64_t stride,
                                 const float *const *in, float *out) {
  // x and y are in[0] and in[1] of a single row
  auto apply = [&](auto op) {
    for (uint64_t idx = 0; idx < stride; ++idx)
      out[idx] = op(in[0][idx], in[1][idx]);
  };

  if (n.t == node::type::constant) {
    std::fill(out, out + stride, n.u.val);
  } else if (n.t == node::type::variable) {
    const float *col = data + (stride * n.u.fid);
    std::copy(col, col + stride, out);
  } else {
    // note: keep the case statements in alphabetical order under each category
    // of operators.
    switch (n.t) {
    // binary operators
    case node::type::add:
      return apply([](float x, float y) { return x + y; });
    case node::type::atan2:
      return apply([](float x, float y) { return atan2f(x, y); });
    case node::type::div:
      return apply([](float x, float y) { return fabsf(y) < MIN_VAL ? 1.0f : (x / y); });
    case node::type::fdim:
      return apply([](float x, float y) { return fdimf(x, y); });
    case node::type::gt:
      return apply([](float x, float y) { return x > y ? 1.0f : 0.0f; });
    case node::type::max:
      return apply([](float x, float y) { return fmaxf(x, y); });
    case node::type::min:
      return apply([](float x, float y) { return fminf(x, y); });
    case node::type::mul:
      return apply([](float x, float y) { return x * y; });
    case node::type::pow:
      return apply([](float x, float y) { return powf(x, y); });
    case node::type::sub:
      return apply([](float x, float y) { return x - y; });
    // unary operators
    case node::type::abs:
      return apply([](float x, float) { return fabsf(x); });
    case node::type::acos:
      return apply([](float x, float) { return acosf(x); });
    case node::type::acosh:
      return apply([](float x, float) { return acoshf(x); });
    case node::type::asin:
      return apply([](float x, float) { return asinf(x); });
    case node::type::asinh:
      return apply([](float x, float) { return asinhf(x); });
    case node::type::atan:
      return apply([](float x, float) { return atanf(x); });
    case node::type::atanh:
      return apply([](float x, float) { return atanhf(x); });
    case node::type::cbrt:
      return apply([](float x, float) { return cbrtf(x); });
    case node::type::cos:
      return apply([](float x, float) { return cosf(x); });
    case node::type::cosh:
      return apply([](float x, float) { return coshf(x); });
    case node::type::cube:
      return apply([](float x, float) { return x * x * x; });
    case node::type::exp:
      return apply([](float x, float) { return expf(x); });
    case node::type::inv:
      return apply([](float x, float) { return fabsf(x) < MIN_VAL ? 0.f : 1.f / x; });
    case node::type::log:
      return apply([](float x, float) { return fabsf(x) < MIN_VAL ? 0.f : logf(fabsf(x)); });
    case node::type::neg:
      return apply([](float x, float) { return -x; });
    case node::type::rcbrt:
      return apply([](float x, float) { return static_cast<float>(1.0) / cbrtf(x); });
    case node::type::rsqrt:
      return apply([](float x, float) { return static_cast<float>(1.0) / sqrtf(fabsf(x)); });
    case node::type::sin:
      return apply([](float x, float) { return sinf(x); });
    case node::type::sinh:
      return apply([](float x, float) { return sinhf(x); });
    case node::type::sq:
      return apply([](float x, float) { return x * x; });
    case node::type::sqrt:
      return apply([](float x, float) { return sqrtf(fabsf(x)); });
    case node::type::tan:
      return apply([](float x, float) { return tanf(x); });
    case node::type::tanh:
      return apply([](float x, float) { return tanhf(x); });
    // shouldn't reach here!
    default:
      return std::fill(out, out + stride, 0.f);
    };
  }
}

} // namespace detail
} // namespace genetic
