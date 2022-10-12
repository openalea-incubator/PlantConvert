from . import np
from . import npl

from . import pgl

class TRSError(Exception):
    pass

def random_matrix4():
    """
    This method returns a random TRS matrix.
    This is for test.
    """
    A = np.identity(4)
    A[:3,:] =1 - 2*np.random.rand(3,4)
    Q,R = npl.qr(A[:3,:3])
    if npl.det(Q) > 0:
        Q[:,0] = -Q[:,0]
        R[0,:] = - R[0,:]

    A[:3,:3] = Q * R.diagonal()
    return A

def numpy_to_mat4(A):
    """ Convert the 2d array A to pgl.Matrix4 object
    
    Input : 
    A : a 2d numpy array. Accepted shape = 3*4, 4*4, 3*3
    
    Output : 
    Mat : the corresponding Matrix4 object. """

    if not (A.shape in [(3,4),(4,4),(3,3)]):
        raise ValueError('The input\'s shape %s %s is not accepted. Must be : 3*4, 4*4 or 3*3'%(A.shape))
    if A.shape == (3,4) or A.shape == (4,4):
        return pgl.Matrix4(*A.T.tolist())
    else:
        return pgl.Matrix4(pgl.Matrix3(*A.flatten().tolist()))

def mat4_to_numpy(A):
    return np.array([[A[i,j] for j in range(4)] for i in range(4)])

def TRS_from_matrix4(A : np.ndarray):
    """
    This method return the TRS components of a TRS matrix  
    """
    rs = A[:3,:3]
    t = A[:3,3]
    s = npl.norm(rs, axis = 0)
    zero_ind = np.isclose(s, 0)
    non_zero_ind = np.logical_not(zero_ind)
    if np.sum(zero_ind) > 1:
        # more than one zero scaling => can't determine the rotation matrix
        raise TRSError("There are more than 2 zero scaling.")

    elif np.sum(zero_ind) == 1:
        # there is only one zero scaling => deduce the axis by cross product
        zero_ind = np.nonzero(zero_ind)[0]
        Q = np.empty((3,3))
        Q[:,non_zero_ind] = rs[:,non_zero_ind] / s[non_zero_ind]
        v1 = Q[:,non_zero_ind][:,0]
        v2 = Q[:,non_zero_ind][:,1]
        Q[:, zero_ind] = np.cross(v1, v2).reshape((3,1))
    else:
        Q = rs / s

    if npl.det(Q) < 0:
        first_non_zero = np.nonzero(non_zero_ind)[0]
        Q[:,first_non_zero] = - Q[:,first_non_zero]
        s[first_non_zero] = -s[first_non_zero]

    return t,Q,s

def inv_TRS(A : np.ndarray):
    """
    This method return the inverse of a TRS matrix.
    """
    t,r,s = TRS_from_matrix4(A)
    inv = np.identity(4)
    
    if np.any(np.isclose(s, 0)):
        raise TRSError("Can't invert TRS when there is 0 scaling")

    inv[:3,3] = - (r.T @ t)/s
    inv[:3,:3] = (r/s).T
    return inv


def is_TRS(A : np.ndarray):
    """
    Test if the input matrix A is a 4D TRS matrix.
    This requires to test if A's linear part is the composition of a rotation and a scaling. If this is the case, the first three columns should be orthogonal. 
    """

    M = A[:3,:3].T@A[:3,:3]
    return np.all(M == np.diag(np.diagonal(M)))

def global_to_local_matrix(mat_c, mat_p = None):
    if mat_p is None:
        return global_to_local_matrix(mat_c, np.identity(4))
    
    else:
        mat_c_np = mat4_to_numpy(mat_c)
        if not isinstance(mat_p, np.ndarray):
            mat_p_np = mat4_to_numpy(mat_p)
        else:
            mat_p_np = mat_p

        return inv_TRS(mat_p_np)@mat_c_np 