# Quick reference guide for converting print() to logger

#

# USAGE PATTERNS:

#

# 1. Informational messages:

# print("Something happened") → logger.info("Something happened")

#

# 2. Warnings:

# print("WARNING: ...") → logger.warning("...")

#

# 3. Errors:

# print("ERROR: ...") → logger.error("...")

#

# 4. Success messages:

# print("✓ Success") → logger.info("✓ Success")

#

# 5. Debug/verbose:

# print(f"Debug: {var}") → logger.debug(f"Debug: {var}")

#

# Key replacements for main.py:

"""
Priority print() statements to replace:

HIGH PRIORITY (errors & warnings):

- Line 176: print(f"[Fatal Error] ...") → logger.error(...)
- Line 143-146: Error messages → logger.error(...)

MEDIUM PRIORITY (user-facing info):

- Line 33: print(f"Mengin isi...") → logger.info(...)
- Line 72: print(f"Cache Soal...") → logger.info(...)
- Line 95: print("Mode --scrape...") → logger.info(...)

LOW PRIORITY (verbose/debug):

- Line 44-46: Part detection → logger.debug(...) or logger.info(...)
- Line 47: Process start → logger.info(...)
  """
