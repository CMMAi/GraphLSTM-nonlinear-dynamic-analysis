import torch


GRAVITY = 9.81              # m/s2
CONCRETE_DENSITY = 2400     # 2400 kg/m3
STEEL_DENSITY = 8050        # 8050 kg/m3
SLAB_THICKNESS = 0.15       # m


class Node:
    def __init__(self, environment_parameters=None, name=None, coord=[0, 0, 0], dof=0, load=[0, 0, 0],
                 node_neighbor_member_list=None, member_category_list=None, member_section_list=None,
                 beam_sections=None, column_sections=None):

        self.x_grid, self.y_grid, self.z_grid, self.x_grid_space, self.y_grid_space, self.z_grid_space = environment_parameters
        self.name = name
        self.x, self.y, self.z = coord
        self.dof = dof
        self.load_x, self.load_y, self.load_z = load
        self.node_neighbor_member_list = node_neighbor_member_list
        self.member_category_list = member_category_list
        self.member_section_list = member_section_list
        self.beam_sections = beam_sections
        self.column_sections = column_sections

        self.self_weight = 0 
        self.translational_mass = 0 
        self.Rx, self.Ry, self.Rz = 0, 0, 0
        
        self.calculate_slab_weight()
        self.calculate_beam_column_weight()
        self.calculate_translational_weight()
        
        slab_list = self.get_neighbor_slab()
        self.calculate_moment_inertia_slab(slab_list)
            
        
    def calculate_slab_weight(self):
        width_x = self.x_grid[1]/2 if self.x == min(self.x_grid) or self.x == max(self.x_grid) else self.x_grid[1]
        width_z = self.z_grid[1]/2 if self.z == min(self.z_grid) or self.z == max(self.z_grid) else self.z_grid[1]
        area = width_x/1000 * width_z/1000  # m2
        slab_weight = area * SLAB_THICKNESS * CONCRETE_DENSITY * GRAVITY / 1000  # kN
        # print(f"Slab weight = {slab_weight}")
        self.self_weight += slab_weight    
        

    def calculate_beam_column_weight(self):
        beam_length_x = self.x_grid[1]/2
        beam_length_z = self.z_grid[1]/2
        column_length = 3200 / 2
        for member_index in self.node_neighbor_member_list:
            member_category = self.member_category_list[member_index]
            section_index = self.member_section_list[member_index]
            section_area = self.column_sections[section_index]['A(cm2)'] if member_category == 'y' else self.beam_sections[section_index]['A(cm2)']
            if member_category == 'x':
                member_weight = section_area/100/100 * beam_length_x/1000 * STEEL_DENSITY * GRAVITY / 1000  # kN
            elif member_category == 'z':
                member_weight = section_area/100/100 * beam_length_z/1000 * STEEL_DENSITY * GRAVITY / 1000  # kN
            elif member_category == 'y':
                member_weight = section_area/100/100 * column_length/1000 * STEEL_DENSITY * GRAVITY / 1000  # kN
            self.self_weight += member_weight
    
        
    def calculate_translational_weight(self):
        kN = self.self_weight
        kg = kN * 1000 / GRAVITY
        self.translational_mass = kg / 1e+06    

        # By the way get load_y
        self.load_y = -1 * self.self_weight          
        
        
       
    def get_neighbor_slab(self):
        # Return each slab with a center point, fixed width1, fixed width2
        slab_list = []
        
        if self.x == min(self.x_grid):
            if self.z == min(self.z_grid):
                slab_list.append([self.x + self.x_grid_space/2, self.y, self.z + self.z_grid_space/2])
            elif self.z == max(self.z_grid):
                slab_list.append([self.x + self.x_grid_space/2, self.y, self.z - self.z_grid_space/2])
            else:
                slab_list.append([self.x + self.x_grid_space/2, self.y, self.z + self.z_grid_space/2])
                slab_list.append([self.x + self.x_grid_space/2, self.y, self.z - self.z_grid_space/2])
                
        elif self.x == max(self.x_grid):
            if self.z == min(self.z_grid):
                slab_list.append([self.x - self.x_grid_space/2, self.y, self.z + self.z_grid_space/2])
            elif self.z == max(self.z_grid):
                slab_list.append([self.x - self.x_grid_space/2, self.y, self.z - self.z_grid_space/2])
            else:
                slab_list.append([self.x - self.x_grid_space/2, self.y, self.z + self.z_grid_space/2])
                slab_list.append([self.x - self.x_grid_space/2, self.y, self.z - self.z_grid_space/2]) 
                
        else:
            if self.z == min(self.z_grid):
                slab_list.append([self.x - self.x_grid_space/2, self.y, self.z + self.z_grid_space/2])
                slab_list.append([self.x + self.x_grid_space/2, self.y, self.z + self.z_grid_space/2])
            elif self.z == max(self.z_grid):
                slab_list.append([self.x - self.x_grid_space/2, self.y, self.z - self.z_grid_space/2])
                slab_list.append([self.x + self.x_grid_space/2, self.y, self.z - self.z_grid_space/2])
            else:
                slab_list.append([self.x - self.x_grid_space/2, self.y, self.z + self.z_grid_space/2])
                slab_list.append([self.x + self.x_grid_space/2, self.y, self.z + self.z_grid_space/2])
                slab_list.append([self.x - self.x_grid_space/2, self.y, self.z - self.z_grid_space/2])
                slab_list.append([self.x + self.x_grid_space/2, self.y, self.z - self.z_grid_space/2])
        
        return slab_list
    
    

    def calculate_moment_inertia_slab(self, slab_list):
        for slab in slab_list:
            slab_mass = self.x_grid_space/1000 * self.z_grid_space/1000 * SLAB_THICKNESS * CONCRETE_DENSITY   # kg
                
            slab_global_Ix = 1 / 12 * slab_mass * ((SLAB_THICKNESS*1000) ** 2 + self.z_grid_space ** 2) / 1e+06 
            slab_global_Iy = 1 / 12 * slab_mass * (self.x_grid_space ** 2 + self.z_grid_space ** 2) / 1e+06 
            slab_global_Iz = 1 / 12 * slab_mass * ((SLAB_THICKNESS*1000) ** 2 + self.x_grid_space ** 2) / 1e+06 
            
            self.Rx += slab_global_Ix / 4
            self.Ry += slab_global_Iy / 4
            self.Rz += slab_global_Iz / 4








                
class RigidZone:
    def __init__(self, node_name, timestep):
        self.name = node_name
        self.face_dict = {}
        self.section_dim = 16
        
        # Each node, there are 6 faces: x_n, x_p, y_n, y_p, z_n, z_p.   p, n is for positive, negative.
        # In each face, there are moment, shear, plastic hinge.
        self.face_dict['x_n'] = dict({'momentY':torch.zeros(timestep), 'momentZ':torch.zeros(timestep), 'shearY':torch.zeros(timestep), 'shearZ':torch.zeros(timestep), 'plastic_hinge_My':torch.zeros(timestep), 'plastic_hinge_Mz':torch.zeros(timestep), 'length':0, 'Myield':0})
        self.face_dict['x_p'] = dict({'momentY':torch.zeros(timestep), 'momentZ':torch.zeros(timestep), 'shearY':torch.zeros(timestep), 'shearZ':torch.zeros(timestep), 'plastic_hinge_My':torch.zeros(timestep), 'plastic_hinge_Mz':torch.zeros(timestep), 'length':0, 'Myield':0})
        self.face_dict['y_n'] = dict({'momentY':torch.zeros(timestep), 'momentZ':torch.zeros(timestep), 'shearY':torch.zeros(timestep), 'shearZ':torch.zeros(timestep), 'plastic_hinge_My':torch.zeros(timestep), 'plastic_hinge_Mz':torch.zeros(timestep), 'length':0, 'Myield':0})
        self.face_dict['y_p'] = dict({'momentY':torch.zeros(timestep), 'momentZ':torch.zeros(timestep), 'shearY':torch.zeros(timestep), 'shearZ':torch.zeros(timestep), 'plastic_hinge_My':torch.zeros(timestep), 'plastic_hinge_Mz':torch.zeros(timestep), 'length':0, 'Myield':0})
        self.face_dict['z_n'] = dict({'momentY':torch.zeros(timestep), 'momentZ':torch.zeros(timestep), 'shearY':torch.zeros(timestep), 'shearZ':torch.zeros(timestep), 'plastic_hinge_My':torch.zeros(timestep), 'plastic_hinge_Mz':torch.zeros(timestep), 'length':0, 'Myield':0})
        self.face_dict['z_p'] = dict({'momentY':torch.zeros(timestep), 'momentZ':torch.zeros(timestep), 'shearY':torch.zeros(timestep), 'shearZ':torch.zeros(timestep), 'plastic_hinge_My':torch.zeros(timestep), 'plastic_hinge_Mz':torch.zeros(timestep), 'length':0, 'Myield':0})

