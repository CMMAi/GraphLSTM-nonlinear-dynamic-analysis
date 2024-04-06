'''
beam section:
(1)     W21x93
(2)     W21x83
(3)     W21x73
(4)     W21x68
(5)     W21x62
(6)     W21x57
(7)     W21x50
(8)     W21x48
(9)     W21x44

column section:
(1)     16x16x0.875
(2)     16x16x0.75
(3)     16x16x0.625
(4)     16x16x0.5
(5)     16x16x0.375

'''


YIELDING_STRESS = 350 # 350 MPa = 350 x 10^3 kN/m^2, so My (kN x mm) = S (cm^3) x 350 (MPa) --> kN x mm

# I-section shape factor = 1.12 ~ 1.14
# Rectangular shape factor = 1.5
BEAM_SHAPE_FACTOR = 1.12
COLUMN_SHAPE_FACTOR = 1.5





beam_sections = []
column_sections = []


# Various Beam, Column section
beam_sections.append({
     'name': 'W21x44',
     'H(mm)': 525.780,
     'B(mm)': 165.100,
     't_f(mm)': 11.430,
     't_w(mm)': 8.890,
     'A(cm2)': 83.871,
     'J(cm4)': 32.050,
     'I_y(cm4)': 861.599,
     'I_z(cm4)': 35088.309,
     'S_y(cm3)': 167.148,
     'S_z(cm3)': 1563.326,
     'Av_y(cm2)': 0.6 * 46.742,
     'Av_z(cm2)': 0.6 * 25.161,
     'My_z(kN-mm)': 1563.326 * YIELDING_STRESS,
     'Z_z(cm3)': 1563.326 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 1563.326 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [157, 227, 245]
})

beam_sections.append({
     'name': 'W21x48',
     'H(mm)': 523.240,
     'B(mm)': 206.756,
     't_f(mm)': 10.922,
     't_w(mm)': 8.890,
     'A(cm2)': 90.968,
     'J(cm4)': 33.423,
     'I_y(cm4)': 1610.816,
     'I_z(cm4)': 39916.594,
     'S_y(cm3)': 244.167,
     'S_z(cm3)': 1753.416,
     'Av_y(cm2)': 0.6 * 46.516,
     'Av_z(cm2)': 0.6 * 30.109,
     'My_z(kN-mm)': 1753.416 * YIELDING_STRESS,
     'Z_z(cm3)': 1753.416 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 1753.416 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [133, 184, 245]
})

beam_sections.append({
     'name': 'W21x50',
     'H(mm)': 528.320,
     'B(mm)': 165.862,
     't_f(mm)': 13.589,
     't_w(mm)': 9.652,
     'A(cm2)': 94.839,
     'J(cm4)': 47.450,
     'I_y(cm4)': 1036.416,
     'I_z(cm4)': 40957.172,
     'S_y(cm3)': 199.922,
     'S_z(cm3)': 1802.577,
     'Av_y(cm2)': 0.6 * 50.993,
     'Av_z(cm2)': 0.6 * 30.052,
     'My_z(kN-mm)': 1802.577 * YIELDING_STRESS,
     'Z_z(cm3)': 1802.577 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 1802.577 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [72, 92, 223]
})

beam_sections.append({
     'name': 'W21x57',
     'H(mm)': 535.940,
     'B(mm)': 166.264,
     't_f(mm)': 16.510,
     't_w(mm)': 10.287,
     'A(cm2)': 107.742,
     'J(cm4)': 73.673,
     'I_y(cm4)': 1273.668,
     'I_z(cm4)': 48699.077,
     'S_y(cm3)': 242.529,
     'S_z(cm3)': 2113.931,
     'Av_y(cm2)': 0.6 * 55.132,
     'Av_z(cm2)': 0.6 * 36.679,
     'My_z(kN-mm)': 2113.931 * YIELDING_STRESS,
     'Z_z(cm3)': 2113.931 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 2113.931 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [37, 12, 211]
})

beam_sections.append({
     'name': 'W21x62',
     'H(mm)': 533.400,
     'B(mm)': 209.296,
     't_f(mm)': 15.621,
     't_w(mm)': 10.160,
     'A(cm2)': 118.064,
     'J(cm4)': 76.170,
     'I_y(cm4)': 2393.331,
     'I_z(cm4)': 55358.780,
     'S_y(cm3)': 355.599,
     'S_z(cm3)': 2359.737,
     'Av_y(cm2)': 0.6 * 54.193,
     'Av_z(cm2)': 0.6 * 43.952,
     'My_z(kN-mm)': 2359.737 * YIELDING_STRESS,
     'Z_z(cm3)': 2359.737 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 2359.737 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [59, 6, 196]
})

beam_sections.append({
     'name': 'W21x68',
     'H(mm)': 535.940,
     'B(mm)': 210.058,
     't_f(mm)': 17.399,
     't_w(mm)': 10.922,
     'A(cm2)': 129.032,
     'J(cm4)': 101.977,
     'I_y(cm4)': 2693.017,
     'I_z(cm4)': 61602.251,
     'S_y(cm3)': 399.844,
     'S_z(cm3)': 2621.930,
     'Av_y(cm2)': 0.6 * 58.535,
     'Av_z(cm2)': 0.6 * 48.731,
     'My_z(kN-mm)': 2621.930 * YIELDING_STRESS,
     'Z_z(cm3)': 2621.930 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 2621.930 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [135, 25, 159]
})

beam_sections.append({
     'name': 'W21x73',
     'H(mm)': 538.480,
     'B(mm)': 210.820,
     't_f(mm)': 18.796,
     't_w(mm)': 11.557,
     'A(cm2)': 138.709,
     'J(cm4)': 125.702,
     'I_y(cm4)': 2938.594,
     'I_z(cm4)': 66597.028,
     'S_y(cm3)': 435.896,
     'S_z(cm3)': 2818.575,
     'Av_y(cm2)': 0.6 * 62.232,
     'Av_z(cm2)': 0.6 * 52.834,
     'My_z(kN-mm)': 2818.575 * YIELDING_STRESS,
     'Z_z(cm3)': 2818.575 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 2818.575 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [148, 28, 147]
})

beam_sections.append({
     'name': 'W21x83',
     'H(mm)': 543.560,
     'B(mm)': 212.344,
     't_f(mm)': 21.209,
     't_w(mm)': 13.081,
     'A(cm2)': 157.419,
     'J(cm4)': 180.644,
     'I_y(cm4)': 3388.124,
     'I_z(cm4)': 76170.351,
     'S_y(cm3)': 499.805,
     'S_z(cm3)': 3211.865,
     'Av_y(cm2)': 0.6 * 71.103,
     'Av_z(cm2)': 0.6 * 60.048,
     'My_z(kN-mm)': 3211.865 * YIELDING_STRESS,
     'Z_z(cm3)': 3211.865 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 3211.865 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [111, 26, 109]
})

beam_sections.append({
     'name': 'W21x93',
     'H(mm)': 548.640,
     'B(mm)': 213.868,
     't_f(mm)': 23.622,
     't_w(mm)': 14.372,
     'A(cm2)': 176.129,
     'J(cm4)': 250.988,
     'I_y(cm4)': 3866.790,
     'I_z(cm4)': 86159.905,
     'S_y(cm3)': 568.631,
     'S_z(cm3)': 3621.541,
     'Av_y(cm2)': 0.6 * 80.826,
     'Av_z(cm2)': 0.6 * 67.360,
     'My_z(kN-mm)': 3621.541 * YIELDING_STRESS,
     'Z_z(cm3)': 3621.541 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 3621.541 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [90, 24, 90]
})





column_sections.append({
     'name': '16x16x0.375',
     'H(mm)': 406.40,
     'B(mm)': 406.40,
     't_f(mm)': 9.50,
     't_w(mm)': 9.50,
     'A(cm2)': 138.71,
     'J(cm4)': 72674.01,
     'I_y(cm4)': 36337.00,
     'I_z(cm4)': 36337.00,
     'S_y(cm3)': 1786.19,
     'S_z(cm3)': 1786.19,
     'Av_y(cm2)': 0.6 * 56.21,
     'Av_z(cm2)': 0.6 * 56.21,
     'My_z(kN-mm)': 1786.19 * YIELDING_STRESS,
     'Z_z(cm3)': 1786.19 * COLUMN_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 1786.19 * COLUMN_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [237, 245, 80]            
})

column_sections.append({
     'name': '16x16x0.5',
     'H(mm)': 406.40,
     'B(mm)': 406.40,
     't_f(mm)': 12.70,
     't_w(mm)': 12.70,
     'A(cm2)': 182.58,
     'J(cm4)': 94068.30,
     'I_y(cm4)': 47034.15,
     'I_z(cm4)': 47034.15,
     'S_y(cm3)': 2310.58,
     'S_z(cm3)': 2310.58,
     'Av_y(cm2)': 0.6 * 75.05,
     'Av_z(cm2)': 0.6 * 75.05,
     'My_z(kN-mm)': 2310.58 * YIELDING_STRESS,
     'Z_z(cm3)': 2310.58 * COLUMN_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 2310.58 * COLUMN_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [189, 247, 78]            
})

column_sections.append({
     'name': '16x16x0.625',
     'H(mm)': 406.40,
     'B(mm)': 406.40,
     't_f(mm)': 15.90,
     't_w(mm)': 15.90,
     'A(cm2)': 225.81,
     'J(cm4)': 114047.41,
     'I_y(cm4)': 57023.71,
     'I_z(cm4)': 57023.71,
     'S_y(cm3)': 2802.19,
     'S_z(cm3)': 2802.19,
     'Av_y(cm2)': 0.6 * 93.85,
     'Av_z(cm2)': 0.6 * 93.85,
     'My_z(kN-mm)': 2802.19 * YIELDING_STRESS,
     'Z_z(cm3)': 2802.19 * COLUMN_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 2802.19 * COLUMN_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [149, 227, 69]              
})

column_sections.append({
     'name': '16x16x0.75',
     'H(mm)': 406.40,
     'B(mm)': 406.40,
     't_f(mm)': 19.00,
     't_w(mm)': 19.00,
     'A(cm2)': 267.74,
     'J(cm4)': 132361.59,
     'I_y(cm4)': 66180.80,
     'I_z(cm4)': 66180.80,
     'S_y(cm3)': 3261.03,
     'S_z(cm3)': 3261.03,
     'Av_y(cm2)': 0.6 * 112.12,
     'Av_z(cm2)': 0.6 * 112.12,
     'My_z(kN-mm)': 3261.03 * YIELDING_STRESS,
     'Z_z(cm3)': 3261.03 * COLUMN_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 3261.03 * COLUMN_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [108, 195, 58]               
})

column_sections.append({
     'name': '16x16x0.875',
     'H(mm)': 406.40,
     'B(mm)': 406.40,
     't_f(mm)': 22.20,
     't_w(mm)': 22.20,
     'A(cm2)': 307.74,
     'J(cm4)': 149843.31,
     'I_y(cm4)': 74921.66,
     'I_z(cm4)': 74921.66,
     'S_y(cm3)': 3687.09,
     'S_z(cm3)': 3687.09,
     'Av_y(cm2)': 0.6 * 131.20,
     'Av_z(cm2)': 0.6 * 131.20,
     'My_z(kN-mm)': 3687.09 * YIELDING_STRESS,
     'Z_z(cm3)': 3687.09 * COLUMN_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 3687.09 * COLUMN_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [54, 123, 32]             
})









"""
-----------------------------------------------------------------------------------------------------------------
"""





beam_section_dict = {}
column_section_dict = {}


# Various Beam, Column section
beam_section_dict['W21x44'] = {
     'H(mm)': 525.780,
     'B(mm)': 165.100,
     't_f(mm)': 11.430,
     't_w(mm)': 8.890,
     'A(cm2)': 83.871,
     'J(cm4)': 32.050,
     'I_y(cm4)': 861.599,
     'I_z(cm4)': 35088.309,
     'S_y(cm3)': 167.148,
     'S_z(cm3)': 1563.326,
     'Av_y(cm2)': 0.6 * 46.742,
     'Av_z(cm2)': 0.6 * 25.161,
     'My_z(kN-mm)': 1563.326 * YIELDING_STRESS,
     'Z_z(cm3)': 1563.326 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 1563.326 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [157, 227, 245]
}

beam_section_dict['W21x48'] = {
     'H(mm)': 523.240,
     'B(mm)': 206.756,
     't_f(mm)': 10.922,
     't_w(mm)': 8.890,
     'A(cm2)': 90.968,
     'J(cm4)': 33.423,
     'I_y(cm4)': 1610.816,
     'I_z(cm4)': 39916.594,
     'S_y(cm3)': 244.167,
     'S_z(cm3)': 1753.416,
     'Av_y(cm2)': 0.6 * 46.516,
     'Av_z(cm2)': 0.6 * 30.109,
     'My_z(kN-mm)': 1753.416 * YIELDING_STRESS,
     'Z_z(cm3)': 1753.416 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 1753.416 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [133, 184, 245]
}

beam_section_dict['W21x50'] = {
     'H(mm)': 528.320,
     'B(mm)': 165.862,
     't_f(mm)': 13.589,
     't_w(mm)': 9.652,
     'A(cm2)': 94.839,
     'J(cm4)': 47.450,
     'I_y(cm4)': 1036.416,
     'I_z(cm4)': 40957.172,
     'S_y(cm3)': 199.922,
     'S_z(cm3)': 1802.577,
     'Av_y(cm2)': 0.6 * 50.993,
     'Av_z(cm2)': 0.6 * 30.052,
     'My_z(kN-mm)': 1802.577 * YIELDING_STRESS,
     'Z_z(cm3)': 1802.577 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 1802.577 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [72, 92, 223]
}

beam_section_dict['W21x57'] = {
     'H(mm)': 535.940,
     'B(mm)': 166.264,
     't_f(mm)': 16.510,
     't_w(mm)': 10.287,
     'A(cm2)': 107.742,
     'J(cm4)': 73.673,
     'I_y(cm4)': 1273.668,
     'I_z(cm4)': 48699.077,
     'S_y(cm3)': 242.529,
     'S_z(cm3)': 2113.931,
     'Av_y(cm2)': 0.6 * 55.132,
     'Av_z(cm2)': 0.6 * 36.679,
     'My_z(kN-mm)': 2113.931 * YIELDING_STRESS,
     'Z_z(cm3)': 2113.931 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 2113.931 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [37, 12, 211]
}

beam_section_dict['W21x62'] = {
     'H(mm)': 533.400,
     'B(mm)': 209.296,
     't_f(mm)': 15.621,
     't_w(mm)': 10.160,
     'A(cm2)': 118.064,
     'J(cm4)': 76.170,
     'I_y(cm4)': 2393.331,
     'I_z(cm4)': 55358.780,
     'S_y(cm3)': 355.599,
     'S_z(cm3)': 2359.737,
     'Av_y(cm2)': 0.6 * 54.193,
     'Av_z(cm2)': 0.6 * 43.952,
     'My_z(kN-mm)': 2359.737 * YIELDING_STRESS,
     'Z_z(cm3)': 2359.737 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 2359.737 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [59, 6, 196]
}

beam_section_dict['W21x68'] = {
     'H(mm)': 535.940,
     'B(mm)': 210.058,
     't_f(mm)': 17.399,
     't_w(mm)': 10.922,
     'A(cm2)': 129.032,
     'J(cm4)': 101.977,
     'I_y(cm4)': 2693.017,
     'I_z(cm4)': 61602.251,
     'S_y(cm3)': 399.844,
     'S_z(cm3)': 2621.930,
     'Av_y(cm2)': 0.6 * 58.535,
     'Av_z(cm2)': 0.6 * 48.731,
     'My_z(kN-mm)': 2621.930 * YIELDING_STRESS,
     'Z_z(cm3)': 2621.930 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 2621.930 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [135, 25, 159]
}

beam_section_dict['W21x73'] = {
     'H(mm)': 538.480,
     'B(mm)': 210.820,
     't_f(mm)': 18.796,
     't_w(mm)': 11.557,
     'A(cm2)': 138.709,
     'J(cm4)': 125.702,
     'I_y(cm4)': 2938.594,
     'I_z(cm4)': 66597.028,
     'S_y(cm3)': 435.896,
     'S_z(cm3)': 2818.575,
     'Av_y(cm2)': 0.6 * 62.232,
     'Av_z(cm2)': 0.6 * 52.834,
     'My_z(kN-mm)': 2818.575 * YIELDING_STRESS,
     'Z_z(cm3)': 2818.575 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 2818.575 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [148, 28, 147]
}

beam_section_dict['W21x83'] = {
     'H(mm)': 543.560,
     'B(mm)': 212.344,
     't_f(mm)': 21.209,
     't_w(mm)': 13.081,
     'A(cm2)': 157.419,
     'J(cm4)': 180.644,
     'I_y(cm4)': 3388.124,
     'I_z(cm4)': 76170.351,
     'S_y(cm3)': 499.805,
     'S_z(cm3)': 3211.865,
     'Av_y(cm2)': 0.6 * 71.103,
     'Av_z(cm2)': 0.6 * 60.048,
     'My_z(kN-mm)': 3211.865 * YIELDING_STRESS,
     'Z_z(cm3)': 3211.865 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 3211.865 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [111, 26, 109]
}

beam_section_dict['W21x93'] = {
     'H(mm)': 548.640,
     'B(mm)': 213.868,
     't_f(mm)': 23.622,
     't_w(mm)': 14.372,
     'A(cm2)': 176.129,
     'J(cm4)': 250.988,
     'I_y(cm4)': 3866.790,
     'I_z(cm4)': 86159.905,
     'S_y(cm3)': 568.631,
     'S_z(cm3)': 3621.541,
     'Av_y(cm2)': 0.6 * 80.826,
     'Av_z(cm2)': 0.6 * 67.360,
     'My_z(kN-mm)': 3621.541 * YIELDING_STRESS,
     'Z_z(cm3)': 3621.541 * BEAM_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 3621.541 * BEAM_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [90, 24, 90]
}





column_section_dict['16x16x0.375'] = {
     'H(mm)': 406.40,
     'B(mm)': 406.40,
     't_f(mm)': 9.50,
     't_w(mm)': 9.50,
     'A(cm2)': 138.71,
     'J(cm4)': 72674.01,
     'I_y(cm4)': 36337.00,
     'I_z(cm4)': 36337.00,
     'S_y(cm3)': 1786.19,
     'S_z(cm3)': 1786.19,
     'Av_y(cm2)': 0.6 * 56.21,
     'Av_z(cm2)': 0.6 * 56.21,
     'My_z(kN-mm)': 1786.19 * YIELDING_STRESS,
     'Z_z(cm3)': 1786.19 * COLUMN_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 1786.19 * COLUMN_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [237, 245, 80]            
}

column_section_dict['16x16x0.5'] = {
     'H(mm)': 406.40,
     'B(mm)': 406.40,
     't_f(mm)': 12.70,
     't_w(mm)': 12.70,
     'A(cm2)': 182.58,
     'J(cm4)': 94068.30,
     'I_y(cm4)': 47034.15,
     'I_z(cm4)': 47034.15,
     'S_y(cm3)': 2310.58,
     'S_z(cm3)': 2310.58,
     'Av_y(cm2)': 0.6 * 75.05,
     'Av_z(cm2)': 0.6 * 75.05,
     'My_z(kN-mm)': 2310.58 * YIELDING_STRESS,
     'Z_z(cm3)': 2310.58 * COLUMN_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 2310.58 * COLUMN_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [189, 247, 78]            
}

column_section_dict['16x16x0.625'] = {
     'H(mm)': 406.40,
     'B(mm)': 406.40,
     't_f(mm)': 15.90,
     't_w(mm)': 15.90,
     'A(cm2)': 225.81,
     'J(cm4)': 114047.41,
     'I_y(cm4)': 57023.71,
     'I_z(cm4)': 57023.71,
     'S_y(cm3)': 2802.19,
     'S_z(cm3)': 2802.19,
     'Av_y(cm2)': 0.6 * 93.85,
     'Av_z(cm2)': 0.6 * 93.85,
     'My_z(kN-mm)': 2802.19 * YIELDING_STRESS,
     'Z_z(cm3)': 2802.19 * COLUMN_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 2802.19 * COLUMN_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [149, 227, 69]              
}

column_section_dict['16x16x0.75'] = {
     'H(mm)': 406.40,
     'B(mm)': 406.40,
     't_f(mm)': 19.00,
     't_w(mm)': 19.00,
     'A(cm2)': 267.74,
     'J(cm4)': 132361.59,
     'I_y(cm4)': 66180.80,
     'I_z(cm4)': 66180.80,
     'S_y(cm3)': 3261.03,
     'S_z(cm3)': 3261.03,
     'Av_y(cm2)': 0.6 * 112.12,
     'Av_z(cm2)': 0.6 * 112.12,
     'My_z(kN-mm)': 3261.03 * YIELDING_STRESS,
     'Z_z(cm3)': 3261.03 * COLUMN_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 3261.03 * COLUMN_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [108, 195, 58]               
}

column_section_dict['16x16x0.875'] = {
     'H(mm)': 406.40,
     'B(mm)': 406.40,
     't_f(mm)': 22.20,
     't_w(mm)': 22.20,
     'A(cm2)': 307.74,
     'J(cm4)': 149843.31,
     'I_y(cm4)': 74921.66,
     'I_z(cm4)': 74921.66,
     'S_y(cm3)': 3687.09,
     'S_z(cm3)': 3687.09,
     'Av_y(cm2)': 0.6 * 131.20,
     'Av_z(cm2)': 0.6 * 131.20,
     'My_z(kN-mm)': 3687.09 * YIELDING_STRESS,
     'Z_z(cm3)': 3687.09 * COLUMN_SHAPE_FACTOR,
     'Mp_z(kN-mm)': 3687.09 * COLUMN_SHAPE_FACTOR * YIELDING_STRESS,
     'color': [54, 123, 32]             
}




 
