# define a api_module STATIC and OBJECT
set(SOURCE_FILES ${CMAKE_CURRENT_SOURCE_DIR}/src/api.cpp)
add_library(api_module STATIC ${SOURCE_FILES})
add_library(api_module_shared SHARED ${SOURCE_FILES})
add_library(api_module_obj OBJECT ${SOURCE_FILES})
# define header file
target_include_directories(api_module PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_include_directories(api_module_obj PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_include_directories(api_module_shared PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

# install api_module
install(TARGETS api_module DESTINATION lib)
install(TARGETS api_module_shared DESTINATION lib)
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/include/ DESTINATION include)
