ret = p.apply(func, (1,))
print(ret)
ret = p.apply(func, (2,))
print(ret)
ret = p.apply(func, (3,))
print(ret)
ret = p.apply(func, (4,))
print(ret)
ret = p.apply(func, (5,))
print(ret)

delta_t = time.time() - start
print("Time :", delta_t)

p.close()
p.join()
# Result

# Running
# on
# Process
# SpawnPoolWorker - 3
# PID
# 18264
# Ended
# 1
# Process
# SpawnPoolWorker - 3
# 1
# Running
# on
# Process
# SpawnPoolWorker - 1
# PID
# 9620
# Ended
# 2
# Process
# SpawnPoolWorker - 1
# 2
# Running
# on
# Process
# SpawnPoolWorker - 2
# PID
# 20172
# Ended
# 3
# Process
# SpawnPoolWorker - 2
# 3
# Running
# on
# Process
# SpawnPoolWorker - 4
# PID
# 11964
# Ended
# 4
# Process
# SpawnPoolWorker - 4
# 4
# Running
# on
# Process
# SpawnPoolWorker - 3
# PID
# 18264
# Ended
# 5
# Process
# SpawnPoolWorker - 3
# 5
# Time: 5.0882182121276855