! Lorenz ' 96 system

module Lorenz96
	
contains

subroutine Xnp1(X,D,Xnp1_res,M)

        
    implicit none
	integer, intent(in) :: D
	real(kind=8), optional :: M
	real(kind=8), intent(in), dimension(D) :: X
    real(kind=8), dimension(D):: k1, k2, k3, k4
	real(kind=8), intent(out), dimension(D-3) :: Xnp1_res
    real(kind=8), dimension(D-3):: ddt
	integer :: i
	real(kind=8) :: dt
	
	if(present(M) .eqv. .false.) then
		M = 8.1d0
	end if
	dt = 0.01d0
		
    call dXdt(X,D,ddt,M)
    k1(3:D-1) = dt*ddt
    k1(1) = k1(D-2)
    k1(2) = k1(D-1)
    k1(D) = k1(3)
    call dXdt(X+0.5d0*k1,D,ddt,M)
    k2(3:D-1) = dt*ddt
    k2(1) = k2(D-2)
    k2(2) = k2(D-1)
    k2(D) = k2(3)
    call dXdt(X+0.5d0*k2,D,ddt,M)
    k3(3:D-1) = dt*ddt
    k3(1) = k3(D-2)
    k3(2) = k3(D-1)
    k3(D) = k3(3)
    call dXdt(X+k3,D,ddt,M)
    k4(3:D-1) = dt*ddt
    
    Xnp1_res = X(3:D-1) + 1.d0/6.d0*k1(3:D-1) + &
               1.d0/3.d0*k2(3:D-1) + 1.d0/3.d0*k3(3:D-1) + &
                1.d0/6.d0*k4(3:D-1)    



end subroutine Xnp1
subroutine dXdt(X,D,Xnp1_res,M)
    implicit none
	integer, intent(in) :: D
	real(kind=8), optional :: M
	real(kind=8), intent(in), dimension(D) :: X
	real(kind=8), intent(out), dimension(D-3) :: Xnp1_res
	integer :: i
	real(kind=8) :: dt
    
    dt = 0.01d0
    if(present(M) .eqv. .false.) then
		M = 8.1d0
	end if

    do i=3,D-1
		Xnp1_res(i-2) = (-X(i-2) + X(i+1))*X(i-1) - X(i) + M	
	end do

    
end subroutine dXdt
subroutine dfdX(X,D,dfdX_res)

	implicit none
	integer, intent(in) :: D
	real(kind=8), intent(in), dimension(D) :: X
	real(kind=8), intent(out), dimension(D-3,D-3) :: dfdX_res 	
	integer :: i,j

	dfdX_res = 0.d0
	do j=3,D-4
		i = j + 2	
		dfdX_res(j,j) = -1.d0
		dfdX_res(j,j-1) = -X(i-2) + X(i+1)
		dfdX_res(j,j+1) = X(i-1)
		dfdX_res(j,j-2) = -X(i-1)  					

	enddo	
 
	dfdX_res(1,1) = -1.d0
	dfdX_res(1,2) = X(2)
	dfdX_res(2,2) = -1.d0	 	
	dfdX_res(2,1) = X(5) - X(2)
	dfdX_res(2,3) = X(3)	
	
	dfdX_res(D-3,D-3) = -1.d0
	dfdX_res(D-3,D-4) = X(D) - X(D-3)
	dfdX_res(D-3,D-5) = -X(D-2) 
    
end subroutine dfdX  

subroutine dvdt(X,D,v1,dvdt_res)

		implicit none
		integer, intent(in) :: D
		real(kind=8), intent(in), dimension(D) :: X
		real(kind=8), intent(out), dimension(D-3,1) :: dvdt_res
		real(kind=8), dimension(D-3,D-3) :: dfdX_res
		real(kind=8), intent(in), dimension(D,1) :: v1
		real(kind=8), dimension(D-3,D) :: dfdX_ext
		integer :: i		
	
		call dfdX(X,D,dfdX_res)
		dfdX_ext = 0.d0
		dfdX_ext(1:D-3,3:D-1) = dfdX_res
	
		dfdX_ext(1,2) = X(4) - X(1)
		dfdX_ext(1,1) = -X(2)  				
	
		dfdX_ext(2,1) = -X(3) 	
		dfdX_ext(D-3,D) = X(D-2) 
		
		dvdt_res = matmul(dfdX_ext,v1) + 1.d0	
end subroutine dvdt
subroutine rk45_full(X,D,v,vnp1)
!Assumes full perturbation vector.
	implicit none
	integer, intent(in) :: D
	real(kind=8) , intent(in), dimension(D) :: X,v
	real(kind=8) , intent(out), dimension(D-3,1) :: vnp1
	real(kind=8) , dimension(D,1) :: v1,k1,k2,k3,k4
	real(kind=8) , dimension(D-3,1):: dvdt_res
	real(kind=8) :: dt

    

	dt = 0.01d0	
	v1 = reshape(v,[D,1])
	call dvdt(X,D,v1,dvdt_res)	
	k1(3:D-1,1) = dt*dvdt_res(:,1)
	k1(1,1) = k1(D-2,1)
	k1(2,1) = k1(D-1,1)
	k1(D,1) = k1(3,1)
	call dvdt(X,D,v1 + 0.5d0*k1,dvdt_res)
	k2(3:D-1,1) = dt*dvdt_res(:,1)
	k2(1,1) = k2(D-2,1)
	k2(2,1) = k2(D-1,1)
	k2(D,1) = k2(3,1)
	call dvdt(X,D,v1 + 0.5d0*k2,dvdt_res)
	k3(3:D-1,1) = dt*dvdt_res(:,1)
	k3(1,1) = k3(D-2,1)
	k3(2,1) = k3(D-1,1)
	k3(D,1) = k3(3,1)
	call dvdt(X,D,v1 + k3,dvdt_res)
	k4(3:D-1,1) = dt*dvdt_res(:,1)
	vnp1(:,1) = v1(3:D-1,1) + 1.d0/6.d0*k1(3:D-1,1) + &
		 1.d0/3.d0*k2(3:D-1,1) + 1.d0/3.d0*k3(3:D-1,1) + &
		1.d0/6.d0*k4(3:D-1,1)
    

end subroutine rk45_full 

end module Lorenz96
